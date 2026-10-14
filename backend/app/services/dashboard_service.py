"""
AquaWatch AI - Dashboard Analytics Service

Performs high-performance database-level aggregations and queries for:
- Public high-level dashboard summaries
- Chemical/physical parameter statistical overviews
- Recent measurement activity stream
- Authorized official / administrative analytics
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, WaterBody, WaterQualityRecord
from app.schemas import (
    DashboardSummaryResponse,
    OfficialDashboardSummaryResponse,
    ParameterStatistic,
    RecentMeasurementItem,
    WaterQualityOverviewResponse,
)


def get_public_summary(db: Session) -> DashboardSummaryResponse:
    """
    Computes high-level platform metrics for public display using SQL aggregate functions.
    """
    total_wb = db.query(func.count(WaterBody.id)).scalar() or 0

    mapped_wb = (
        db.query(func.count(WaterBody.id))
        .filter(
            WaterBody.latitude.isnot(None),
            WaterBody.longitude.isnot(None),
            WaterBody.latitude >= -90.0,
            WaterBody.latitude <= 90.0,
            WaterBody.longitude >= -180.0,
            WaterBody.longitude <= 180.0,
        )
        .scalar()
        or 0
    )

    total_meas = db.query(func.count(WaterQualityRecord.id)).scalar() or 0

    latest_ts = db.query(func.max(WaterQualityRecord.measured_at)).scalar()

    active_locations = (
        db.query(func.count(func.distinct(WaterQualityRecord.water_body_id))).scalar() or 0
    )

    return DashboardSummaryResponse(
        total_water_bodies=total_wb,
        mapped_locations=mapped_wb,
        total_measurements=total_meas,
        latest_measurement_timestamp=latest_ts,
        active_monitoring_locations=active_locations,
    )


def get_water_quality_overview(
    db: Session,
    water_body_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> WaterQualityOverviewResponse:
    """
    Calculates parameter averages across actual stored records.
    Ignores null values in accordance with standard SQL AVG() semantics.
    Returns null if no measurements exist for a parameter.
    """
    query = db.query(
        func.count(WaterQualityRecord.id).label("total_records"),
        func.max(WaterQualityRecord.measured_at).label("latest_ts"),
        func.avg(WaterQualityRecord.ph).label("avg_ph"),
        func.avg(WaterQualityRecord.dissolved_oxygen).label("avg_do"),
        func.avg(WaterQualityRecord.bod).label("avg_bod"),
        func.avg(WaterQualityRecord.turbidity).label("avg_turbidity"),
        func.avg(WaterQualityRecord.tds).label("avg_tds"),
        func.avg(WaterQualityRecord.electrical_conductivity).label("avg_ec"),
        func.avg(WaterQualityRecord.nitrate).label("avg_nitrate"),
        func.avg(WaterQualityRecord.temperature).label("avg_temp"),
    )

    if water_body_id is not None:
        query = query.filter(WaterQualityRecord.water_body_id == water_body_id)

    if start_date is not None:
        query = query.filter(WaterQualityRecord.measured_at >= start_date)

    if end_date is not None:
        query = query.filter(WaterQualityRecord.measured_at <= end_date)

    row = query.one()

    def format_stat(val: Optional[float], unit: str) -> ParameterStatistic:
        return ParameterStatistic(
            value=round(val, 2) if val is not None else None,
            unit=unit,
        )

    return WaterQualityOverviewResponse(
        total_records_analyzed=row.total_records or 0,
        latest_measurement_timestamp=row.latest_ts,
        average_ph=format_stat(row.avg_ph, "dimensionless"),
        average_dissolved_oxygen=format_stat(row.avg_do, "mg/L"),
        average_bod=format_stat(row.avg_bod, "mg/L"),
        average_turbidity=format_stat(row.avg_turbidity, "NTU"),
        average_tds=format_stat(row.avg_tds, "mg/L"),
        average_electrical_conductivity=format_stat(row.avg_ec, "µS/cm"),
        average_nitrate=format_stat(row.avg_nitrate, "mg/L"),
        average_temperature=format_stat(row.avg_temp, "°C"),
    )


def get_recent_measurements(
    db: Session,
    limit: int = 10,
) -> List[RecentMeasurementItem]:
    """
    Retrieves the most recent water quality records, joined with water body context.
    """
    rows = (
        db.query(WaterQualityRecord, WaterBody)
        .join(WaterBody, WaterQualityRecord.water_body_id == WaterBody.id)
        .order_by(WaterQualityRecord.measured_at.desc())
        .limit(limit)
        .all()
    )

    result: List[RecentMeasurementItem] = []
    for record, wb in rows:
        result.append(
            RecentMeasurementItem(
                id=record.id,
                water_body_id=record.water_body_id,
                water_body_name=wb.name,
                water_body_type=wb.water_body_type,
                location_name=wb.location_name,
                ph=record.ph,
                dissolved_oxygen=record.dissolved_oxygen,
                bod=record.bod,
                turbidity=record.turbidity,
                tds=record.tds,
                electrical_conductivity=record.electrical_conductivity,
                nitrate=record.nitrate,
                temperature=record.temperature,
                measured_at=record.measured_at,
                created_at=record.created_at,
            )
        )

    return result


def get_official_summary(db: Session) -> OfficialDashboardSummaryResponse:
    """
    Computes authorized administrative and regulatory analytics.
    """
    public_summary = get_public_summary(db)

    # Water bodies with zero measurements
    unmonitored_count = (
        db.query(func.count(WaterBody.id))
        .filter(~WaterBody.records.any())
        .scalar()
        or 0
    )

    now_utc = datetime.now(timezone.utc)
    seven_days_ago = now_utc - timedelta(days=7)
    thirty_days_ago = now_utc - timedelta(days=30)

    last_7_days = (
        db.query(func.count(WaterQualityRecord.id))
        .filter(WaterQualityRecord.measured_at >= seven_days_ago)
        .scalar()
        or 0
    )

    last_30_days = (
        db.query(func.count(WaterQualityRecord.id))
        .filter(WaterQualityRecord.measured_at >= thirty_days_ago)
        .scalar()
        or 0
    )

    total_users = db.query(func.count(User.id)).scalar() or 0

    role_counts_raw = (
        db.query(User.role, func.count(User.id))
        .group_by(User.role)
        .all()
    )
    users_by_role = {str(role.value if hasattr(role, 'value') else role): count for role, count in role_counts_raw}

    return OfficialDashboardSummaryResponse(
        public_summary=public_summary,
        unmonitored_water_bodies_count=unmonitored_count,
        measurements_last_7_days=last_7_days,
        measurements_last_30_days=last_30_days,
        total_registered_users=total_users,
        users_by_role=users_by_role,
    )
