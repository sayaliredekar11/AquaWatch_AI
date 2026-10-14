"""
AquaWatch AI - GIS & Mapping Service

Encapsulates data retrieval for map-based visualizations:
- Retrieves water bodies with valid geographic coordinates
- Efficiently fetches the latest measurement for each location (avoiding N+1 queries)
- Integrates with the classification service for status indicators
- Formats data cleanly for Leaflet.js / OpenStreetMap frontend components
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.models import WaterBody, WaterQualityRecord
from app.schemas import GISLocationDetail, GISLocationMarker, MeasurementSnapshot, WaterQualityRecordResponse
from app.services.water_quality_classifier import classify_water_quality


def get_monitoring_locations(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    water_body_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[GISLocationMarker]:
    """
    Retrieves all water bodies with valid geographic coordinates, paired with their
    latest available water-quality measurement.
    """
    # 1. Base filter: Must have valid, non-null latitude and longitude within real world bounds
    query = db.query(WaterBody).filter(
        WaterBody.latitude.isnot(None),
        WaterBody.longitude.isnot(None),
        WaterBody.latitude >= -90.0,
        WaterBody.latitude <= 90.0,
        WaterBody.longitude >= -180.0,
        WaterBody.longitude <= 180.0,
    )

    # 2. Filter by water body type if provided
    if water_body_type:
        query = query.filter(func.lower(WaterBody.water_body_type) == water_body_type.strip().lower())

    # 3. Filter by measurement date range if provided
    if start_date or end_date:
        meas_filters = []
        if start_date:
            meas_filters.append(WaterQualityRecord.measured_at >= start_date)
        if end_date:
            meas_filters.append(WaterQualityRecord.measured_at <= end_date)
        query = query.filter(WaterBody.records.any(and_(*meas_filters)))

    # 4. Fetch paginated water bodies
    water_bodies = query.order_by(WaterBody.id.asc()).offset(skip).limit(limit).all()
    if not water_bodies:
        return []

    wb_ids = [wb.id for wb in water_bodies]

    # 5. Fetch the latest measurement for each water body using PostgreSQL's DISTINCT ON
    # This guarantees exactly 1 efficient database query regardless of page size.
    stmt = (
        select(WaterQualityRecord)
        .filter(WaterQualityRecord.water_body_id.in_(wb_ids))
    )
    if start_date:
        stmt = stmt.filter(WaterQualityRecord.measured_at >= start_date)
    if end_date:
        stmt = stmt.filter(WaterQualityRecord.measured_at <= end_date)

    stmt = stmt.ext(distinct_on(WaterQualityRecord.water_body_id)).order_by(
        WaterQualityRecord.water_body_id,
        WaterQualityRecord.measured_at.desc(),
    )

    latest_records = db.scalars(stmt).all()
    latest_by_wb = {rec.water_body_id: rec for rec in latest_records}

    # 6. Assemble map markers
    markers: List[GISLocationMarker] = []
    for wb in water_bodies:
        rec = latest_by_wb.get(wb.id)
        status, reason = classify_water_quality(rec)

        snapshot: Optional[MeasurementSnapshot] = None
        latest_measured_at: Optional[datetime] = None

        if rec:
            latest_measured_at = rec.measured_at
            snapshot = MeasurementSnapshot(
                ph=rec.ph,
                dissolved_oxygen=rec.dissolved_oxygen,
                bod=rec.bod,
                turbidity=rec.turbidity,
                tds=rec.tds,
                electrical_conductivity=rec.electrical_conductivity,
                nitrate=rec.nitrate,
                temperature=rec.temperature,
            )

        markers.append(
            GISLocationMarker(
                water_body_id=wb.id,
                name=wb.name,
                water_body_type=wb.water_body_type,
                location_name=wb.location_name,
                latitude=wb.latitude,
                longitude=wb.longitude,
                latest_measured_at=latest_measured_at,
                latest_measurements=snapshot,
                water_quality_status=status,
                status_reason=reason,
            )
        )

    return markers


def get_location_detail(
    db: Session,
    water_body_id: int,
    recent_limit: int = 10,
) -> Optional[GISLocationDetail]:
    """
    Retrieves full location metadata and recent measurement history for a specific map marker.
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    if not water_body:
        return None

    # Fetch recent measurement records
    recent_records = (
        db.query(WaterQualityRecord)
        .filter(WaterQualityRecord.water_body_id == water_body_id)
        .order_by(WaterQualityRecord.measured_at.desc())
        .limit(recent_limit)
        .all()
    )

    latest_rec = recent_records[0] if recent_records else None
    status, reason = classify_water_quality(latest_rec)

    snapshot: Optional[MeasurementSnapshot] = None
    latest_measured_at: Optional[datetime] = None

    if latest_rec:
        latest_measured_at = latest_rec.measured_at
        snapshot = MeasurementSnapshot(
            ph=latest_rec.ph,
            dissolved_oxygen=latest_rec.dissolved_oxygen,
            bod=latest_rec.bod,
            turbidity=latest_rec.turbidity,
            tds=latest_rec.tds,
            electrical_conductivity=latest_rec.electrical_conductivity,
            nitrate=latest_rec.nitrate,
            temperature=latest_rec.temperature,
        )

    formatted_recent = [
        WaterQualityRecordResponse.model_validate(r) for r in recent_records
    ]

    return GISLocationDetail(
        water_body_id=water_body.id,
        name=water_body.name,
        water_body_type=water_body.water_body_type,
        location_name=water_body.location_name,
        latitude=water_body.latitude,
        longitude=water_body.longitude,
        created_at=water_body.created_at,
        latest_measured_at=latest_measured_at,
        latest_measurements=snapshot,
        water_quality_status=status,
        status_reason=reason,
        recent_measurements=formatted_recent,
    )
