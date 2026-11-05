"""
AquaWatch AI - Water Quality Records Router

CRUD operations for physical, chemical, and biological water quality parameter measurements.

Role-Based Access:
- View (GET /water-quality, GET /water-quality/{id}) : NORMAL_USER, LAB_AUTHORITY
- Create (POST /water-quality)                       : LAB_AUTHORITY
- Update (PATCH /water-quality/{id})                 : LAB_AUTHORITY
- Delete (DELETE /water-quality/{id})                : Restricted (HTTP 403)
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.schemas import (
    PredictionInput,
    WaterQualityRecordCreate,
    WaterQualityRecordResponse,
    WaterQualityRecordUpdate,
    WaterQualityTestRequest,
    WaterQualityTestResponse,
    WaterTestingReportSummary,
    WaterTestingReportListResponse,
)
from app.security import get_current_user, require_roles
from app.services.pdf_report_service import pdf_report_service, get_wqi_category
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
# 2B. Deprecated Demo Test Samples Endpoint
# ==========================================================
@router.get(
    "/demo-samples",
    response_model=List[Dict[str, Any]],
    summary="List predefined dummy water quality test samples (Deprecated)",
)
def get_dummy_test_samples():
    """
    Deprecated endpoint: Mock/dummy samples have been completely removed.
    Returns an empty list in accordance with strict genuine laboratory data requirements.
    """
    return []


# ==========================================================
# 2C. Test Water Quality Sample & Generate Certified PDF Report
# ==========================================================
@router.post(
    "/test",
    response_model=WaterQualityTestResponse,
    summary="Validate, test sample, predict WQI, persist record, and generate PDF report",
)
async def test_water_quality_sample(
    payload: WaterQualityTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Submits a water quality sample for laboratory testing, ML prediction, and PDF reporting:
    - Allowed roles: LAB_AUTHORITY only
    - Validates required monitoring location (location_id / water_body_id)
    - Validates 14 laboratory measurements and bounds
    - Predicts WQI using trained DecisionTreeRegressor (12 model features)
    - Computes Water Quality Category (Grade A through E)
    - Evaluates rule-based drinking water safety screening (SAFE / HARMFUL / INCONCLUSIVE)
    - Persists complete test record to PostgreSQL (never overwriting historical results)
    - Automatically generates professional A4 PDF report in backend storage
    - Returns comprehensive test response with download URL
    """
    target_location_id = payload.location_id or payload.water_body_id
    water_body = None

    if payload.save_to_db:
        if not target_location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A monitored geographical location is required (water_body_id is required). Please select a valid monitoring location.",
            )
        water_body = db.query(WaterBody).filter(WaterBody.id == target_location_id).first()
        if not water_body:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitored location with ID {target_location_id} does not exist.",
            )
    else:
        if target_location_id:
            water_body = db.query(WaterBody).filter(WaterBody.id == target_location_id).first()

    # Auto-generate unique Sample ID and Report ID if not provided
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    sample_id = payload.sample_id.strip() if payload.sample_id and payload.sample_id.strip() else f"SMP-{date_str}-{unique_suffix}"
    report_id = f"REP-{date_str}-{unique_suffix}"

    # Laboratory and sample metadata
    lab_authority = (
        payload.lab_authority_name.strip()
        if payload.lab_authority_name and payload.lab_authority_name.strip()
        else getattr(current_user, "name", "Authorized Lab Authority")
    )
    lab_name = (
        payload.laboratory_name.strip()
        if payload.laboratory_name and payload.laboratory_name.strip()
        else "AquaWatch Central Water Testing Lab - Maharashtra"
    )
    test_method = (
        payload.testing_method.strip()
        if payload.testing_method and payload.testing_method.strip()
        else "Standard Methods (APHA / IS 3025)"
    )
    test_date = payload.testing_date or datetime.now(timezone.utc)
    collection_time = payload.sampled_at or test_date
    sample_type = (
        payload.sample_type.strip()
        if payload.sample_type and payload.sample_type.strip()
        else "Surface Water"
    )
    remarks = (
        payload.remarks.strip()
        if payload.remarks and payload.remarks.strip()
        else "Laboratory analysis verified against CPCB Class C & IS 10500 standards."
    )

    chlorides_val = payload.chlorides if payload.chlorides is not None else payload.chloride
    payload.chlorides = chlorides_val

    # Assemble all 14 parameters dictionary (+ ammonia_n)
    parameters_dict = {
        "ph": payload.ph,
        "dissolved_oxygen": payload.dissolved_oxygen,
        "bod": payload.bod,
        "turbidity": payload.turbidity,
        "tds": payload.tds,
        "electrical_conductivity": payload.electrical_conductivity,
        "nitrate": payload.nitrate,
        "temperature": payload.temperature,
        "cod": payload.cod,
        "ammonia_n": payload.ammonia_n,
        "chlorides": chlorides_val,
        "sulphate": payload.sulphate,
        "phosphate": payload.phosphate,
        "fecal_coliform": payload.fecal_coliform,
        "total_coliform": payload.total_coliform,
    }

    # 1. Rule-Based Water Safety Evaluation (CPCB Class C / IS 10500 Baseline)
    safety_eval = evaluate_sample_safety(
        measurements=parameters_dict,
        sample_name=payload.sample_name,
        sample_type=sample_type,
    )

    # 2. Machine Learning WQI Prediction (requires 12 model features)
    ml_feature_keys = [
        "dissolved_oxygen", "ph", "bod", "cod", "nitrate", "ammonia_n",
        "turbidity", "tds", "chlorides", "sulphate", "fecal_coliform", "total_coliform"
    ]
    missing_ml_features = [k for k in ml_feature_keys if getattr(payload, k) is None]

    ml_prediction = None
    prediction_service._refresh_config()
    wqi_score = None
    wqi_category = None
    wqi_status = "UNAVAILABLE"
    algo_name = "Decision Tree Regressor"

    if not missing_ml_features:
        try:
            pred_input = PredictionInput(
                dissolved_oxygen=payload.dissolved_oxygen,
                ph=payload.ph,
                bod=payload.bod,
                cod=payload.cod,
                nitrate=payload.nitrate,
                ammonia_n=payload.ammonia_n,
                turbidity=payload.turbidity,
                tds=payload.tds,
                chlorides=payload.chlorides,
                sulphate=payload.sulphate,
                fecal_coliform=payload.fecal_coliform,
                total_coliform=payload.total_coliform,
            )
            ml_prediction = await prediction_service.predict(pred_input)
            wqi_score = ml_prediction.wqi_score
            wqi_category = get_wqi_category(wqi_score)
            wqi_status = "SUCCESS"
            algo_name = ml_prediction.algorithm or "Decision Tree Regressor"
            ml_model_status = "ACTIVE"
            ml_model_details = (
                f"Trained DecisionTreeRegressor executed successfully. "
                f"Predicted Water Quality Index (WQI): {wqi_score:.2f} ({wqi_category})."
            )
        except Exception as e:
            ml_model_status = "ERROR"
            wqi_status = "ERROR"
            ml_model_details = f"ML model prediction error: {str(e)}"
    else:
        if prediction_service.mode == "none":
            ml_model_status = "UNAVAILABLE"
            ml_model_details = "Machine learning prediction model is currently pending deployment."
        else:
            ml_model_status = "INCOMPLETE_FEATURES"
            ml_model_details = (
                f"ML model requires all 12 parameters to compute WQI. Missing {len(missing_ml_features)} parameter(s): "
                f"{', '.join(missing_ml_features)}."
            )

    persisted = False
    persisted_record_id = None
    pdf_file_path = None
    pdf_download_url = None
    sample_display_name = payload.sample_name or "Lab Sample"

    if payload.save_to_db and water_body:
        # Persist test record into PostgreSQL database (separate historical record)
        new_record = WaterQualityRecord(
            water_body_id=water_body.id,
            ph=payload.ph,
            dissolved_oxygen=payload.dissolved_oxygen,
            bod=payload.bod,
            turbidity=payload.turbidity,
            tds=payload.tds,
            electrical_conductivity=payload.electrical_conductivity,
            nitrate=payload.nitrate,
            temperature=payload.temperature,
            cod=payload.cod,
            ammonia_n=payload.ammonia_n,
            chlorides=payload.chlorides,
            sulphate=payload.sulphate,
            phosphate=payload.phosphate,
            fecal_coliform=payload.fecal_coliform,
            total_coliform=payload.total_coliform,
            sample_name=sample_display_name,
            sample_id=sample_id,
            sample_type=sample_type,
            laboratory_name=lab_name,
            lab_authority_name=lab_authority,
            testing_date=test_date,
            testing_method=test_method,
            remarks=remarks,
            report_id=report_id,
            wqi_score=wqi_score,
            wqi_prediction=f"{wqi_score:.2f}" if wqi_score is not None else None,
            wqi_category=wqi_category,
            wqi_status=wqi_status,
            wqi_algorithm=algo_name if ml_prediction else None,
            safety_classification=safety_eval["classification"],
            measured_at=collection_time,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        persisted = True
        persisted_record_id = new_record.id

        # Generate Formal A4 PDF Report and store in backend storage
        report_dict = {
            "report_id": report_id,
            "sample_id": sample_id,
            "sample_name": new_record.sample_name,
            "sample_type": sample_type,
            "water_body_id": water_body.id,
            "water_body_name": water_body.name,
            "water_body_type": water_body.water_body_type,
            "location_name": water_body.location_name,
            "district": water_body.district or "Maharashtra",
            "state": water_body.state or "Maharashtra",
            "latitude": water_body.latitude,
            "longitude": water_body.longitude,
            "sampled_at": collection_time,
            "testing_date": test_date,
            "laboratory_name": lab_name,
            "lab_authority_name": lab_authority,
            "testing_method": test_method,
            "remarks": remarks,
            "wqi_score": wqi_score,
            "wqi_category": wqi_category,
            "wqi_algorithm": algo_name if ml_prediction else "Decision Tree Regressor",
            "safety_classification": safety_eval["classification"],
            "parameters": parameters_dict,
        }
        pdf_file_path = pdf_report_service.generate_water_test_pdf(report_dict)
        new_record.pdf_path = pdf_file_path
        db.commit()
        db.refresh(new_record)

        pdf_download_url = f"/water-quality/reports/{report_id}/download"

        message = (
            f"Water quality sample '{sample_id}' successfully evaluated for location '{water_body.name}' (#{water_body.id}). "
            f"Safety Classification: {safety_eval['classification']}. "
            + (f"ML WQI: {wqi_score:.2f} ({wqi_category}). " if wqi_score is not None else "")
            + f"Record persisted to PostgreSQL (ID #{new_record.id}) and PDF report generated."
        )
    else:
        message = (
            f"Water quality sample '{sample_display_name}' successfully evaluated. "
            f"Safety Classification: {safety_eval['classification']}. "
            + (f"ML WQI: {wqi_score:.2f} ({wqi_category}). " if wqi_score is not None else "")
            + "Evaluation completed in dry-run mode (not persisted to database)."
        )

    return WaterQualityTestResponse(
        status="SUCCESS",
        classification=safety_eval["classification"],
        safety_status=safety_eval["classification"],
        is_safe=(safety_eval["classification"] == "SAFE"),
        result_type=safety_eval["result_type"],
        sample_name=sample_display_name,
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
        sampled_at=collection_time,
        persisted_to_database=persisted,
        persisted_record_id=persisted_record_id,
        location_id=str(water_body.id) if water_body else None,
        water_body_id=water_body.id if water_body else None,
        location_name=water_body.location_name if water_body else None,
        water_body_name=water_body.name if water_body else None,
        district=water_body.district if water_body else None,
        state=water_body.state if water_body else None,
        sample_id=sample_id,
        sample_type=sample_type,
        laboratory_name=lab_name,
        lab_authority_name=lab_authority,
        testing_date=test_date,
        testing_method=test_method,
        remarks=remarks,
        report_id=report_id,
        pdf_path=pdf_file_path,
        pdf_url=pdf_download_url,
        report_download_url=pdf_download_url,
        wqi_category=wqi_category,
        ml_model_status=ml_model_status,
        ml_model_details=ml_model_details,
        ml_prediction=ml_prediction,
        wqi_score=wqi_score,
        message=message,
    )


# ==========================================================
# 2D. Download Certified PDF Report
# ==========================================================
@router.get(
    "/reports/{report_id}/download",
    summary="Download certified water quality laboratory PDF report",
)
def download_water_test_report_pdf(
    report_id: str,
    db: Session = Depends(get_db),
):
    """
    Downloads the official A4 PDF report generated for a water test record:
    - Resolves by Report ID (e.g. REP-20261104-XXXX) or Sample ID (SMP-20261104-XXXX) or Record ID
    - Returns application/pdf file stream
    - Dynamically generates the PDF if record exists but PDF file is not on disk
    """
    clean_id = report_id.strip()
    record = (
        db.query(WaterQualityRecord)
        .filter(
            (WaterQualityRecord.report_id == clean_id)
            | (WaterQualityRecord.sample_id == clean_id)
        )
        .first()
    )
    if not record and clean_id.isdigit():
        record = db.query(WaterQualityRecord).filter(WaterQualityRecord.id == int(clean_id)).first()

    target_file = pdf_report_service.get_report_file_path(clean_id)

    if not os.path.exists(target_file):
        if record and record.pdf_path and os.path.exists(record.pdf_path):
            target_file = record.pdf_path
        elif record:
            wb = record.water_body
            regen_data = {
                "report_id": record.report_id or clean_id,
                "sample_id": record.sample_id or f"SMP-{record.id}",
                "sample_name": record.sample_name or "Lab Sample",
                "sample_type": record.sample_type or "Surface Water",
                "water_body_id": record.water_body_id,
                "water_body_name": wb.name if wb else "Monitored Water Body",
                "water_body_type": wb.water_body_type if wb else "River",
                "location_name": wb.location_name if wb else "",
                "district": wb.district if wb else "",
                "state": wb.state if wb else "Maharashtra",
                "latitude": wb.latitude if wb else None,
                "longitude": wb.longitude if wb else None,
                "sampled_at": record.measured_at,
                "testing_date": record.testing_date or record.measured_at,
                "laboratory_name": record.laboratory_name or "AquaWatch Central Water Testing Lab - Maharashtra",
                "lab_authority_name": record.lab_authority_name or "Authorized Lab Authority",
                "testing_method": record.testing_method or "Standard Methods (APHA / IS 3025)",
                "remarks": record.remarks or "Historical record retrieved from PostgreSQL.",
                "wqi_score": record.wqi_score,
                "wqi_category": record.wqi_category or get_wqi_category(record.wqi_score),
                "wqi_algorithm": record.wqi_algorithm or "Decision Tree Regressor",
                "safety_classification": record.safety_classification or "SAFE",
                "parameters": {
                    "ph": record.ph,
                    "dissolved_oxygen": record.dissolved_oxygen,
                    "bod": record.bod,
                    "turbidity": record.turbidity,
                    "tds": record.tds,
                    "electrical_conductivity": record.electrical_conductivity,
                    "nitrate": record.nitrate,
                    "temperature": record.temperature,
                    "cod": record.cod,
                    "ammonia_n": record.ammonia_n,
                    "chlorides": record.chlorides,
                    "sulphate": record.sulphate,
                    "phosphate": record.phosphate,
                    "fecal_coliform": record.fecal_coliform,
                    "total_coliform": record.total_coliform,
                },
            }
            target_file = pdf_report_service.generate_water_test_pdf(regen_data)
            record.pdf_path = target_file
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Water testing report with identifier '{clean_id}' was not found.",
            )

    filename = f"{clean_id}.pdf" if not clean_id.endswith(".pdf") else clean_id
    return FileResponse(
        path=target_file,
        media_type="application/pdf",
        filename=filename,
    )


# ==========================================================
# 2E. List Previous Water Testing Reports (Search & Audit)
# ==========================================================
@router.get(
    "/reports",
    response_model=WaterTestingReportListResponse,
    summary="List and search previous water testing reports",
)
def list_water_testing_reports(
    skip: int = Query(0, ge=0, description="Offset number of reports to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of reports to return"),
    search: Optional[str] = Query(None, description="Search by Sample ID, Report ID, or water body name"),
    water_body_id: Optional[int] = Query(None, description="Optional water body filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves previous water testing records and PDF report metadata:
    - Allowed roles: All authenticated users (NORMAL_USER, LAB_AUTHORITY)
    - Supports search by Sample ID (e.g. SMP-...), Report ID (e.g. REP-...), or location name
    - Returns paginated list with direct PDF download URLs
    """
    query = db.query(WaterQualityRecord)

    if water_body_id:
        query = query.filter(WaterQualityRecord.water_body_id == water_body_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (WaterQualityRecord.sample_id.ilike(term))
            | (WaterQualityRecord.report_id.ilike(term))
            | (WaterQualityRecord.sample_name.ilike(term))
            | (WaterQualityRecord.water_body.has(WaterBody.name.ilike(term)))
            | (WaterQualityRecord.water_body.has(WaterBody.location_name.ilike(term)))
            | (WaterQualityRecord.water_body.has(WaterBody.district.ilike(term)))
        )

    total = query.count()
    records = (
        query.order_by(WaterQualityRecord.measured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for r in records:
        wb = r.water_body
        rep_id = r.report_id or f"REP-LEGACY-{r.id}"
        smp_id = r.sample_id or f"SMP-LEGACY-{r.id}"
        items.append(
            WaterTestingReportSummary(
                id=r.id,
                report_id=rep_id,
                sample_id=smp_id,
                sample_name=r.sample_name,
                sample_type=r.sample_type or "Surface Water",
                water_body_id=r.water_body_id,
                water_body_name=wb.name if wb else None,
                water_body_type=wb.water_body_type if wb else None,
                location_name=wb.location_name if wb else None,
                district=wb.district if wb else None,
                state=wb.state if wb else None,
                latitude=wb.latitude if wb else None,
                longitude=wb.longitude if wb else None,
                measured_at=r.measured_at,
                testing_date=r.testing_date or r.measured_at,
                laboratory_name=r.laboratory_name or "AquaWatch Central Water Testing Lab - Maharashtra",
                lab_authority_name=r.lab_authority_name,
                testing_method=r.testing_method,
                remarks=r.remarks,
                wqi_score=r.wqi_score,
                wqi_category=r.wqi_category or get_wqi_category(r.wqi_score),
                wqi_status=r.wqi_status,
                safety_classification=r.safety_classification,
                pdf_path=r.pdf_path,
                pdf_url=f"/water-quality/reports/{rep_id}/download",
                created_at=r.created_at,
            )
        )

    return WaterTestingReportListResponse(total=total, items=items)


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
