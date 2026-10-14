"""
AquaWatch AI - Dashboard Analytics Router

Provides statistical aggregations and activity feeds for public and authorized official views.

Endpoints:
- GET /dashboard/summary                 : Public platform-wide summary metrics
- GET /dashboard/water-quality-overview  : Statistical averages per parameter (SQL aggregation)
- GET /dashboard/recent-measurements     : Latest measurement feed with location names
- GET /dashboard/official-summary        : Authorized executive/regulatory dashboard
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import (
    DashboardSummaryResponse,
    OfficialDashboardSummaryResponse,
    RecentMeasurementItem,
    WaterQualityOverviewResponse,
)
from app.security import require_roles
from app.services.dashboard_service import (
    get_official_summary,
    get_public_summary,
    get_recent_measurements,
    get_water_quality_overview,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboards & Analytics"])


# ==========================================================
# 1. Public Dashboard Summary
# ==========================================================
@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get high-level platform monitoring summary",
)
def public_dashboard_summary(
    db: Session = Depends(get_db),
):
    """
    Returns platform-wide summary statistics:
    - Total water bodies
    - Mapped locations with coordinates
    - Total recorded measurements
    - Active monitoring locations
    - Publicly accessible
    """
    return get_public_summary(db)


# ==========================================================
# 2. Water Quality Parameter Statistical Overview
# ==========================================================
@router.get(
    "/water-quality-overview",
    response_model=WaterQualityOverviewResponse,
    summary="Get statistical averages for water quality parameters",
)
def water_quality_overview(
    water_body_id: Optional[int] = Query(None, description="Filter statistics for a specific water body"),
    start_date: Optional[datetime] = Query(None, description="Include measurements on or after this timestamp"),
    end_date: Optional[datetime] = Query(None, description="Include measurements on or before this timestamp"),
    db: Session = Depends(get_db),
):
    """
    Returns aggregate averages for physical and chemical water quality parameters.
    - Uses SQL AVG() aggregation across stored PostgreSQL data
    - Ignores null values; returns null if no measurements exist for a parameter
    - Documents measurement units for each parameter
    - Publicly accessible
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date.",
        )

    return get_water_quality_overview(
        db=db,
        water_body_id=water_body_id,
        start_date=start_date,
        end_date=end_date,
    )


# ==========================================================
# 3. Recent Measurements Stream
# ==========================================================
@router.get(
    "/recent-measurements",
    response_model=List[RecentMeasurementItem],
    summary="Get recent water quality measurements with location details",
)
def recent_measurements_feed(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return (max 100)"),
    db: Session = Depends(get_db),
):
    """
    Returns the most recent water quality measurements joined with location context:
    - Ordered by measurement timestamp in descending order
    - Publicly accessible for dashboard activity tables
    """
    return get_recent_measurements(db=db, limit=limit)


# ==========================================================
# 4. Authorized Official Dashboard Summary
# ==========================================================
@router.get(
    "/official-summary",
    response_model=OfficialDashboardSummaryResponse,
    summary="Get authorized regulatory & laboratory administrative summary",
)
def official_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Returns extended management analytics for laboratory authorities:
    - Unmonitored water bodies count
    - Data velocity (measurements logged in last 7 and 30 days)
    - User account counts and breakdown by role
    - Requires LAB_AUTHORITY role
    """
    return get_official_summary(db=db)
