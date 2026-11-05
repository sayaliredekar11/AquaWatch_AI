"""
AquaWatch AI - GIS & Mapping Service

Encapsulates data retrieval for map-based visualizations:
- Retrieves water bodies with valid geographic coordinates from PostgreSQL
- Integrates dedicated synthetic demonstration locations (Maharashtra monitoring network)
- Seamlessly resolves both database water bodies and demo monitoring locations
- Serves latest measurement snapshots and chronological trend history
- Formats data cleanly for Leaflet.js / OpenStreetMap and Recharts frontend components
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.models import WaterBody, WaterQualityRecord
from app.schemas import (
    GISLocationDetail,
    GISLocationMarker,
    LocationHistoryItem,
    LocationHistoryResponse,
    MeasurementSnapshot,
    WaterQualityRecordResponse,
)
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
    Retrieves all monitoring stations with valid coordinates:
    - Queries production PostgreSQL water bodies
    - Appends dedicated Maharashtra demonstration monitoring stations
    - Supports filtering by water_body_type and measurement date range
    """
    # 1. Base DB filter: valid coordinates within real world bounds
    query = db.query(WaterBody).filter(
        WaterBody.latitude.isnot(None),
        WaterBody.longitude.isnot(None),
        WaterBody.latitude >= -90.0,
        WaterBody.latitude <= 90.0,
        WaterBody.longitude >= -180.0,
        WaterBody.longitude <= 180.0,
    )

    if water_body_type:
        query = query.filter(func.lower(WaterBody.water_body_type) == water_body_type.strip().lower())

    if start_date or end_date:
        meas_filters = []
        if start_date:
            meas_filters.append(WaterQualityRecord.measured_at >= start_date)
        if end_date:
            meas_filters.append(WaterQualityRecord.measured_at <= end_date)
        query = query.filter(WaterBody.records.any(and_(*meas_filters)))

    db_water_bodies = query.order_by(WaterBody.id.asc()).all()

    markers: List[GISLocationMarker] = []

    # 2. Process database water bodies
    if db_water_bodies:
        wb_ids = [wb.id for wb in db_water_bodies]
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

        for wb in db_water_bodies:
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
                    cod=rec.cod,
                    ammonia_n=rec.ammonia_n,
                    chlorides=rec.chlorides,
                    sulphate=rec.sulphate,
                    phosphate=rec.phosphate,
                    fecal_coliform=rec.fecal_coliform,
                    total_coliform=rec.total_coliform,
                    wqi_score=rec.wqi_score,
                )

            markers.append(
                GISLocationMarker(
                    water_body_id=wb.id,
                    location_id=str(wb.id),
                    name=wb.name,
                    water_body_type=wb.water_body_type,
                    location_name=wb.location_name,
                    district=wb.district,
                    state=wb.state or "Maharashtra",
                    latitude=wb.latitude,
                    longitude=wb.longitude,
                    latest_measured_at=latest_measured_at,
                    latest_measurements=snapshot,
                    latest_wqi_score=rec.wqi_score if rec else None,
                    latest_wqi_category=rec.wqi_category if rec else None,
                    latest_safety_classification=rec.safety_classification if rec else None,
                    water_quality_status=status,
                    status_reason=reason,
                    is_demo=False,
                )
            )

    # Return paginated markers from PostgreSQL database
    return markers[skip : skip + limit]


def get_location_detail(
    db: Session,
    location_id: Union[int, str],
    recent_limit: int = 15,
) -> Optional[GISLocationDetail]:
    """
    Retrieves full location metadata and recent measurement history for a specific location
    directly from PostgreSQL. Returns None (404) if the location does not exist in the database.
    """
    clean_id = str(location_id).strip()

    try:
        int_id = int(clean_id)
    except ValueError:
        return None

    water_body = db.query(WaterBody).filter(WaterBody.id == int_id).first()
    if not water_body:
        return None

    recent_records = (
        db.query(WaterQualityRecord)
        .filter(WaterQualityRecord.water_body_id == int_id)
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
            cod=latest_rec.cod,
            ammonia_n=latest_rec.ammonia_n,
            chlorides=latest_rec.chlorides,
            sulphate=latest_rec.sulphate,
            phosphate=latest_rec.phosphate,
            fecal_coliform=latest_rec.fecal_coliform,
            total_coliform=latest_rec.total_coliform,
            wqi_score=latest_rec.wqi_score,
        )

    formatted_recent = [
        WaterQualityRecordResponse.model_validate(r) for r in recent_records
    ]

    return GISLocationDetail(
        water_body_id=water_body.id,
        location_id=str(water_body.id),
        name=water_body.name,
        water_body_type=water_body.water_body_type,
        location_name=water_body.location_name,
        district=water_body.district,
        state=water_body.state or "Maharashtra",
        latitude=water_body.latitude,
        longitude=water_body.longitude,
        created_at=water_body.created_at,
        latest_measured_at=latest_measured_at,
        latest_measurements=snapshot,
        latest_wqi_score=latest_rec.wqi_score if latest_rec else None,
        latest_wqi_category=latest_rec.wqi_category if latest_rec else None,
        latest_safety_classification=latest_rec.safety_classification if latest_rec else None,
        water_quality_status=status,
        status_reason=reason,
        is_demo=False,
        recent_measurements=formatted_recent,
    )


def get_location_history_service(
    db: Session,
    location_id: Union[int, str],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> Optional[LocationHistoryResponse]:
    """
    Retrieves chronological historical measurements for trend visualization from PostgreSQL.
    Returns 404 (None) if the location does not exist in the database.
    """
    clean_id = str(location_id).strip()

    try:
        int_id = int(clean_id)
    except ValueError:
        return None

    water_body = db.query(WaterBody).filter(WaterBody.id == int_id).first()
    if not water_body:
        return None

    query = db.query(WaterQualityRecord).filter(WaterQualityRecord.water_body_id == int_id)
    if start_date:
        query = query.filter(WaterQualityRecord.measured_at >= start_date)
    if end_date:
        query = query.filter(WaterQualityRecord.measured_at <= end_date)

    db_records = query.order_by(WaterQualityRecord.measured_at.asc()).limit(limit).all()

    records = [
        LocationHistoryItem(
            id=r.id,
            water_body_id=r.water_body_id,
            location_id=str(r.water_body_id),
            measured_at=r.measured_at,
            ph=r.ph,
            dissolved_oxygen=r.dissolved_oxygen,
            bod=r.bod,
            turbidity=r.turbidity,
            tds=r.tds,
            electrical_conductivity=r.electrical_conductivity,
            nitrate=r.nitrate,
            temperature=r.temperature,
            cod=r.cod,
            ammonia_n=r.ammonia_n,
            chlorides=r.chlorides,
            sulphate=r.sulphate,
            phosphate=r.phosphate,
            fecal_coliform=r.fecal_coliform,
            total_coliform=r.total_coliform,
            sample_name=r.sample_name,
            sample_id=r.sample_id,
            report_id=r.report_id,
            wqi_score=r.wqi_score,
            wqi_category=r.wqi_category,
            wqi_status=r.wqi_status,
            safety_classification=r.safety_classification,
            pdf_path=r.pdf_path,
            is_demo=False,
        )
        for r in db_records
    ]

    latest_rec = db_records[-1] if db_records else None

    return LocationHistoryResponse(
        location_id=str(water_body.id),
        water_body_id=water_body.id,
        name=water_body.name,
        water_body_type=water_body.water_body_type,
        location_name=water_body.location_name,
        district=water_body.district,
        state=water_body.state or "Maharashtra",
        latitude=water_body.latitude,
        longitude=water_body.longitude,
        latest_wqi_score=latest_rec.wqi_score if latest_rec else None,
        latest_wqi_category=latest_rec.wqi_category if latest_rec else None,
        latest_wqi_status=latest_rec.wqi_status if latest_rec else None,
        latest_safety_classification=latest_rec.safety_classification if latest_rec else None,
        is_demo=False,
        total_records=len(records),
        records=records,
    )
