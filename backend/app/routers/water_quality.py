"""
AquaWatch AI - Water Quality Records Router

CRUD operations for physical, chemical, and biological water quality parameter measurements.

Role-Based Access:
- View (GET /water-quality, GET /water-quality/{id}) : NORMAL_USER, LAB_AUTHORITY
- Create (POST /water-quality)                       : LAB_AUTHORITY
- Update (PATCH /water-quality/{id})                 : LAB_AUTHORITY
- Delete (DELETE /water-quality/{id})                : Restricted (HTTP 403)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.demo_data import DUMMY_WATER_QUALITY_SAMPLES
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.schemas import (
    WaterQualityRecordCreate,
    WaterQualityRecordResponse,
    WaterQualityRecordUpdate,
    WaterQualityTestRequest,
    WaterQualityTestResponse,
)
from app.security import get_current_user, require_roles
from app.services.prediction_service import prediction_service
from app.services.water_quality_classifier import evaluate_sample_safety

router = APIRouter(prefix="/water-quality", tags=["Water Quality Records"])


# ==========================================================
# 1. Create a Measurement Record
# ==========================================================
@router.post(
    "",
    response_model=WaterQualityRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a water quality measurement record",
)
def create_water_quality_record(
    payload: WaterQualityRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Records a new water quality sampling measurement:
    - Allowed roles: LAB_AUTHORITY
    - Verifies that the referenced water_body_id exists
    - Validates units and parameter limits (pH 0-14, nonnegative values)
    """
    # Verify foreign key existence
    water_body = db.query(WaterBody).filter(WaterBody.id == payload.water_body_id).first()
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water body with ID {payload.water_body_id} does not exist.",
        )

    record_data = payload.model_dump()
    new_record = WaterQualityRecord(**record_data)

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


# ==========================================================
# 2. Get All Measurement Records (Filtered & Paginated)
# ==========================================================
@router.get(
    "",
    response_model=List[WaterQualityRecordResponse],
    summary="List water quality measurement records with filters and pagination",
)
def list_water_quality_records(
    skip: int = Query(0, ge=0, description="Offset number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    water_body_id: Optional[int] = Query(None, description="Optional filter by water body ID"),
    start_date: Optional[datetime] = Query(None, description="Filter measurements sampled on or after this timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter measurements sampled on or before this timestamp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves water quality measurements:
    - Allowed roles: All authenticated users (CITIZEN, LAB_AUTHORITY, POLLUTION_OFFICIAL, ADMIN)
    - Supports pagination (skip, limit capped at 100)
    - Supports optional filtering by water_body_id and measurement date range
    """
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date range: start_date must be earlier than or equal to end_date.",
        )

    query = db.query(WaterQualityRecord)

    if water_body_id is not None:
        query = query.filter(WaterQualityRecord.water_body_id == water_body_id)

    if start_date is not None:
        query = query.filter(WaterQualityRecord.measured_at >= start_date)

    if end_date is not None:
        query = query.filter(WaterQualityRecord.measured_at <= end_date)

    records = (
        query.order_by(WaterQualityRecord.measured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return records


# ==========================================================
# 2B. Predefined Dummy Test Samples (DEMO DATA)
# ==========================================================
@router.get(
    "/demo-samples",
    response_model=List[Dict[str, Any]],
    summary="List predefined dummy water quality test samples",
)
def get_dummy_test_samples():
    """
    Returns the standard set of illustrative dummy test samples:
    - Sample A: Neutral pH, balanced test parameters
    - Sample B: Acidic pH, elevated BOD and turbidity
    - Sample C: Slightly alkaline pH, moderate solids
    
    COMPLIANCE NOTICE:
    These values are illustrative test inputs, not verified measurements from real water bodies.
    They do not claim that water is safe to drink.
    """
    return DUMMY_WATER_QUALITY_SAMPLES


# ==========================================================
# 2C. Test Water Quality Sample (In-Memory Validation & Testing)
# ==========================================================
@router.post(
    "/test",
    response_model=WaterQualityTestResponse,
    summary="Validate and test a water quality sample",
)
def test_water_quality_sample(
    payload: WaterQualityTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Submits a water quality sample for laboratory validation & testing:
    - Allowed roles: LAB_AUTHORITY only (HTTP 401 unauthenticated, HTTP 403 for NORMAL_USER)
    - Validates numeric parameters and scientific bounds using Pydantic
    - By default, does NOT insert dummy records into PostgreSQL, preventing skew of real monitoring metrics
    - If explicit saving is requested (save_to_db=True), validates water_body_id and persists record
    - Checks ML model integration status and never invents arbitrary predictions or safety claims
    """
    persisted = False
    persisted_record_id = None

    # Handle explicit user persistence action if requested
    if payload.save_to_db:
        if not payload.water_body_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid water_body_id is required when explicit database persistence is requested.",
            )

        water_body = db.query(WaterBody).filter(WaterBody.id == payload.water_body_id).first()
        if not water_body:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitored water body with ID {payload.water_body_id} does not exist.",
            )

        # Explicitly save record to PostgreSQL
        new_record = WaterQualityRecord(
            water_body_id=payload.water_body_id,
            ph=payload.ph,
            dissolved_oxygen=payload.dissolved_oxygen,
            bod=payload.bod,
            turbidity=payload.turbidity,
            tds=payload.tds,
            electrical_conductivity=payload.electrical_conductivity,
            nitrate=payload.nitrate,
            temperature=payload.temperature,
            measured_at=datetime.now(timezone.utc),
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        persisted = True
        persisted_record_id = new_record.id

    # Determine Machine Learning Integration Status
    prediction_service._refresh_config()
    if prediction_service.mock_mode:
        ml_model_status = "MOCK_AVAILABLE"
        ml_model_details = "Backend test mock mode is active (ML_MOCK_MODE=true)."
    elif prediction_service.mode == "none":
        ml_model_status = "UNAVAILABLE"
        ml_model_details = (
            "Machine learning prediction model is currently pending deployment from ML teammate "
            "(ML_INTEGRATION_MODE=none). No fake ML predictions are generated."
        )
    elif prediction_service.mode == "file":
        ml_model_status = "LOCAL_ARTIFACT"
        ml_model_details = f"Local model configured at {prediction_service.model_path}."
    elif prediction_service.mode == "api":
        ml_model_status = "REMOTE_MICROSERVICE"
        ml_model_details = f"External ML endpoint configured at {prediction_service.service_url}."
    else:
        ml_model_status = "UNCONFIGURED"
        ml_model_details = "ML integration mode unrecognized."

    # Assemble parameter dictionary
    parameters_dict = {
        "ph": payload.ph,
        "dissolved_oxygen": payload.dissolved_oxygen,
        "bod": payload.bod,
        "turbidity": payload.turbidity,
        "tds": payload.tds,
        "electrical_conductivity": payload.electrical_conductivity,
        "nitrate": payload.nitrate,
        "temperature": payload.temperature,
    }

    # Execute Rule-Based Water Safety Evaluation (CPCB Class C / IS 10500 Baseline)
    safety_eval = evaluate_sample_safety(
        measurements=parameters_dict,
        sample_name=payload.sample_name,
    )

    message = (
        f"Water quality sample '{payload.sample_name}' successfully evaluated by FastAPI backend. "
        f"Safety Classification: {safety_eval['classification']}. "
        + ("Record was saved to PostgreSQL." if persisted else "Result is an in-memory demo test; not persisted to database.")
    )

    return WaterQualityTestResponse(
        status="SUCCESS",
        classification=safety_eval["classification"],
        result_type=safety_eval["result_type"],
        sample_name=payload.sample_name,
        is_demo=payload.is_demo,
        standard_name=safety_eval["standard_name"],
        standard_intended_use=safety_eval["standard_intended_use"],
        parameters_received=parameters_dict,
        parameter_assessments=safety_eval["parameter_assessments"],
        failed_parameters=safety_eval["failed_parameters"],
        passed_parameters=safety_eval["passed_parameters"],
        reasons=safety_eval["reasons"],
        warnings=safety_eval["warnings"],
        limitations=safety_eval["limitations"],
        evaluated_at=datetime.now(timezone.utc),
        persisted_to_database=persisted,
        persisted_record_id=persisted_record_id,
        ml_model_status=ml_model_status,
        ml_model_details=ml_model_details,
        message=message,
    )


# ==========================================================
# 3. Get a Measurement Record by ID
# ==========================================================
@router.get(
    "/{record_id}",
    response_model=WaterQualityRecordResponse,
    summary="Get a water quality record by ID",
)
def get_water_quality_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a single water quality measurement record:
    - Allowed roles: All authenticated users
    - Returns HTTP 404 if record is not found
    """
    record = db.query(WaterQualityRecord).filter(WaterQualityRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water quality measurement record with ID {record_id} not found.",
        )
    return record


# ==========================================================
# 4. Update a Measurement Record (Partial PATCH)
# ==========================================================
@router.patch(
    "/{record_id}",
    response_model=WaterQualityRecordResponse,
    summary="Partially update a water quality record",
)
def update_water_quality_record(
    record_id: int,
    payload: WaterQualityRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Partially updates an existing water quality measurement record:
    - Allowed roles: LAB_AUTHORITY
    - Updates only fields supplied in the PATCH request
    - Validates that newly supplied water_body_id references an existing water body
    - Returns HTTP 404 if the record does not exist
    """
    record = db.query(WaterQualityRecord).filter(WaterQualityRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water quality measurement record with ID {record_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # If updating the foreign key, verify target water body exists
    if "water_body_id" in update_data and update_data["water_body_id"] is not None:
        target_wb = db.query(WaterBody).filter(WaterBody.id == update_data["water_body_id"]).first()
        if not target_wb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referenced water body with ID {update_data['water_body_id']} does not exist.",
            )

    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)

    return record


# ==========================================================
# 5. Delete a Measurement Record
# ==========================================================
@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a water quality measurement record",
)
def delete_water_quality_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes an existing water quality measurement record:
    - Restricted under two-role policy: deletion is disallowed to preserve scientific audit trails.
    - Requires authentication; returns HTTP 403 Forbidden.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: Deletion of water quality measurement records is restricted under the two-role operational policy.",
    )
