"""
AquaWatch AI - Water Quality Records Router

CRUD operations for physical, chemical, and biological water quality parameter measurements.

Role-Based Access:
- View (GET /water-quality, GET /water-quality/{id}) : NORMAL_USER, LAB_AUTHORITY
- Create (POST /water-quality)                       : LAB_AUTHORITY
- Update (PATCH /water-quality/{id})                 : LAB_AUTHORITY
- Delete (DELETE /water-quality/{id})                : Restricted (HTTP 403)
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.schemas import (
    WaterQualityRecordCreate,
    WaterQualityRecordResponse,
    WaterQualityRecordUpdate,
)
from app.security import get_current_user, require_roles

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
