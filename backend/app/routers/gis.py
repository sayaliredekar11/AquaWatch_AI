"""
AquaWatch AI - GIS & Mapping Router

Provides map marker and location data for Leaflet.js / OpenStreetMap frontend integration.

Endpoints:
- GET /gis/locations               : Public map markers with valid coordinates and latest measurements
- GET /gis/locations/{id}          : Detailed marker view with measurement history
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GISLocationDetail, GISLocationMarker
from app.services.gis_service import get_location_detail, get_monitoring_locations

router = APIRouter(prefix="/gis", tags=["GIS & Maps"])


# ==========================================================
# 1. Get Monitoring Locations for Map Display
# ==========================================================
@router.get(
    "/locations",
    response_model=List[GISLocationMarker],
    summary="Get monitoring locations with valid map coordinates",
)
def list_map_locations(
    water_body_type: Optional[str] = Query(
        None,
        description="Filter by water body type (e.g. river, lake, reservoir)",
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="Filter locations having measurements on or after this timestamp",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter locations having measurements on or before this timestamp",
    ),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Maximum markers to return (max 100)"),
    db: Session = Depends(get_db),
):
    """
    Returns water bodies with valid latitude and longitude coordinates for map rendering.
    - Excludes locations with missing or out-of-bounds coordinates
    - Includes the latest water quality measurement for each location
    - Includes status and reason indicators (UNKNOWN pending regulatory standard)
    - Publicly accessible to support citizen map views
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date.",
        )

    return get_monitoring_locations(
        db=db,
        skip=skip,
        limit=limit,
        water_body_type=water_body_type,
        start_date=start_date,
        end_date=end_date,
    )


# ==========================================================
# 2. Get Location Details and Measurement History
# ==========================================================
@router.get(
    "/locations/{water_body_id}",
    response_model=GISLocationDetail,
    summary="Get location details and recent measurement history for a map marker",
)
def get_map_location_details(
    water_body_id: int,
    recent_limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of recent measurement logs to include",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns complete metadata and recent measurement history for a selected water body marker.
    - Returns HTTP 404 if the water body does not exist
    - Publicly accessible for interactive map popups and side-panels
    """
    detail = get_location_detail(
        db=db,
        water_body_id=water_body_id,
        recent_limit=recent_limit,
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water body with ID {water_body_id} does not exist.",
        )

    return detail
