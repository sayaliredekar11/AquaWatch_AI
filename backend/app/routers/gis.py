"""
AquaWatch AI - GIS & Mapping Router

Provides map marker and location data for Leaflet.js / OpenStreetMap frontend integration.

Endpoints:
- GET /gis/locations                    : Public map markers with valid coordinates and latest measurements
- GET /gis/locations/{location_id}       : Detailed marker view with latest snapshot & recent records
- GET /gis/locations/{location_id}/history: Chronological trend data sequence for Recharts visualization
"""

from datetime import datetime
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GISLocationDetail, GISLocationMarker, LocationHistoryResponse
from app.services.gis_service import (
    get_location_detail,
    get_location_history_service,
    get_monitoring_locations,
)

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
    - Combines verified database stations with distinct Maharashtra demonstration stations
    - Includes the latest water quality measurement for each location
    - Clearly flags synthetic data with is_demo=True
    - Publicly accessible without authentication
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
# 2. Get Location Details and Latest Measurement Summary
# ==========================================================
@router.get(
    "/locations/{location_id}",
    response_model=GISLocationDetail,
    summary="Get location details and measurement snapshot for a map marker",
)
def get_map_location_details(
    location_id: str,
    recent_limit: int = Query(
        15,
        ge=1,
        le=50,
        description="Maximum number of recent measurement logs to include",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns complete metadata and recent measurement history for a selected station.
    - Accepts stable location identifiers (e.g. 'demo_loc_001') or database IDs (e.g. '1')
    - Returns HTTP 404 if the station does not exist in demo or production databases
    - Publicly accessible for interactive map popups and side-panels
    """
    detail = get_location_detail(
        db=db,
        location_id=location_id,
        recent_limit=recent_limit,
    )

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitoring location with ID '{location_id}' does not exist.",
        )

    return detail


# ==========================================================
# 3. Get Chronological Measurement History for Trend Intelligence
# ==========================================================
@router.get(
    "/locations/{location_id}/history",
    response_model=LocationHistoryResponse,
    summary="Get chronological measurement trend history for a specific location",
)
def get_map_location_history(
    location_id: str,
    start_date: Optional[datetime] = Query(
        None,
        description="Filter historical records sampled on or after this timestamp",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="Filter historical records sampled on or before this timestamp",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=200,
        description="Maximum number of historical records to return",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns time-series observations for trend analysis on the Water Quality Intelligence page.
    - Resolves both synthetic demonstration stations and database water bodies
    - Supports date range filtering (start_date, end_date)
    - Returns HTTP 404 if the requested location identifier is unknown
    - Publicly accessible without authentication
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date.",
        )

    history = get_location_history_service(
        db=db,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitoring location with ID '{location_id}' does not exist.",
        )

    return history
