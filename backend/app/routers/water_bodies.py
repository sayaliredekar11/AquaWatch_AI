"""
AquaWatch AI - Water Bodies Router

CRUD operations for monitored water bodies (rivers, lakes, reservoirs, etc.).

Role-Based Access:
- View (GET /water-bodies, GET /water-bodies/{id}) : NORMAL_USER, LAB_AUTHORITY
- Create (POST /water-bodies)                      : LAB_AUTHORITY
- Update (PATCH /water-bodies/{id})                : LAB_AUTHORITY
- Delete (DELETE /water-bodies/{id})               : Restricted (HTTP 403)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.schemas import WaterBodyCreate, WaterBodyResponse, WaterBodyUpdate
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/water-bodies", tags=["Water Bodies"])


# ==========================================================
# 1. Create a Water Body
# ==========================================================
@router.post(
    "",
    response_model=WaterBodyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new monitored water body",
)
def create_water_body(
    payload: WaterBodyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Registers a new monitored water body:
    - Allowed roles: LAB_AUTHORITY
    - Validates geographic coordinates (-90 to 90 lat, -180 to 180 lon)
    """
    new_water_body = WaterBody(
        name=payload.name.strip(),
        water_body_type=payload.water_body_type.strip().lower(),
        location_name=payload.location_name.strip(),
        district=payload.district.strip() if payload.district else None,
        state=payload.state.strip() if payload.state else "Maharashtra",
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    db.add(new_water_body)
    db.commit()
    db.refresh(new_water_body)

    return new_water_body


# ==========================================================
# 2. Get All Water Bodies (Paginated)
# ==========================================================
@router.get(
    "",
    response_model=List[WaterBodyResponse],
    summary="List all monitored water bodies with pagination",
)
def list_water_bodies(
    skip: int = Query(0, ge=0, description="Offset number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all monitored water bodies:
    - Allowed roles: All authenticated users (CITIZEN, LAB_AUTHORITY, POLLUTION_OFFICIAL, ADMIN)
    - Supports pagination via skip and limit query parameters (limit capped at 100)
    """
    return db.query(WaterBody).order_by(WaterBody.id.asc()).offset(skip).limit(limit).all()


# ==========================================================
# 3. Get a Water Body by ID
# ==========================================================
@router.get(
    "/{water_body_id}",
    response_model=WaterBodyResponse,
    summary="Get a water body by ID",
)
def get_water_body(
    water_body_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a single water body by ID:
    - Allowed roles: All authenticated users
    - Returns HTTP 404 if the water body does not exist
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water body with ID {water_body_id} not found.",
        )
    return water_body


# ==========================================================
# 4. Update a Water Body (Partial PATCH)
# ==========================================================
@router.patch(
    "/{water_body_id}",
    response_model=WaterBodyResponse,
    summary="Partially update a water body",
)
def update_water_body(
    water_body_id: int,
    payload: WaterBodyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Partially updates an existing water body:
    - Allowed roles: LAB_AUTHORITY
    - Updates only fields supplied in the PATCH request
    - Returns HTTP 404 if the water body does not exist
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water body with ID {water_body_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(water_body, key, value)

    db.commit()
    db.refresh(water_body)

    return water_body


# ==========================================================
# 5. Delete a Water Body
# ==========================================================
@router.delete(
    "/{water_body_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a water body",
)
def delete_water_body(
    water_body_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes an existing water body:
    - Restricted under two-role policy: deletion is disallowed to prevent loss of monitored locations.
    - Requires authentication; returns HTTP 403 Forbidden.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: Deletion of monitored water bodies is restricted under the two-role operational policy.",
    )
