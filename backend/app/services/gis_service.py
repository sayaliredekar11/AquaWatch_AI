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

from app.demo_data import (
    get_demo_locations_list,
    get_demo_location_by_id,
    get_demo_location_history,
)
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
                    latest_safety_classification=rec.safety_classification if rec else None,
                    water_quality_status=status,
                    status_reason=reason,
                    is_demo=False,
                )
            )

    # 3. Append demonstration monitoring stations from demo_data
    demo_list = get_demo_locations_list()
    for d in demo_list:
        # Check water_body_type filter
        if water_body_type and d["water_body_type"].lower() != water_body_type.strip().lower():
            continue

        latest_meas = d.get("latest_measurements")
        snapshot = None
        if latest_meas:
            snapshot = MeasurementSnapshot(
                ph=latest_meas.get("ph"),
                dissolved_oxygen=latest_meas.get("dissolved_oxygen"),
                bod=latest_meas.get("bod"),
                turbidity=latest_meas.get("turbidity"),
                tds=latest_meas.get("tds"),
                electrical_conductivity=latest_meas.get("electrical_conductivity"),
                nitrate=latest_meas.get("nitrate"),
                temperature=latest_meas.get("temperature"),
            )

        markers.append(
            GISLocationMarker(
                water_body_id=d["location_id"],
                location_id=d["location_id"],
                name=d["name"],
                water_body_type=d["water_body_type"],
                location_name=d["location_name"],
                latitude=d["latitude"],
                longitude=d["longitude"],
                latest_measured_at=d.get("latest_measured_at"),
                latest_measurements=snapshot,
                water_quality_status=d.get("water_quality_status", "DEMO_EVALUATION"),
                status_reason=d.get("status_reason", "Synthetic demonstration station"),
                is_demo=True,
            )
        )

    # Apply pagination offset and limit to final combined markers
    return markers[skip : skip + limit]


def get_location_detail(
    db: Session,
    location_id: Union[int, str],
    recent_limit: int = 15,
) -> Optional[GISLocationDetail]:
    """
    Retrieves full location metadata and recent measurement history for a specific location.
    Resolves both synthetic demonstration stations and PostgreSQL database water bodies.
    """
    clean_id = str(location_id).strip()

    # 1. Check demonstration stations first
    demo_loc = get_demo_location_by_id(clean_id)
    if demo_loc:
        history = demo_loc.get("history", [])
        latest = history[-1] if history else None

        snapshot = None
        if latest:
            snapshot = MeasurementSnapshot(
                ph=latest.get("ph"),
                dissolved_oxygen=latest.get("dissolved_oxygen"),
                bod=latest.get("bod"),
                turbidity=latest.get("turbidity"),
                tds=latest.get("tds"),
                electrical_conductivity=latest.get("electrical_conductivity"),
                nitrate=latest.get("nitrate"),
                temperature=latest.get("temperature"),
            )

        # Recent observations (sorted descending for inspection cards)
        recent_obs = sorted(history, key=lambda x: x["measured_at"], reverse=True)[:recent_limit]
        formatted_recent = [
            LocationHistoryItem(
                id=obs["id"],
                water_body_id=demo_loc["location_id"],
                location_id=demo_loc["location_id"],
                measured_at=obs["measured_at"],
                ph=obs.get("ph"),
                dissolved_oxygen=obs.get("dissolved_oxygen"),
                bod=obs.get("bod"),
                turbidity=obs.get("turbidity"),
                tds=obs.get("tds"),
                electrical_conductivity=obs.get("electrical_conductivity"),
                nitrate=obs.get("nitrate"),
                temperature=obs.get("temperature"),
                is_demo=True,
            )
            for obs in recent_obs
        ]

        return GISLocationDetail(
            water_body_id=demo_loc["location_id"],
            location_id=demo_loc["location_id"],
            name=demo_loc["name"],
            water_body_type=demo_loc["water_body_type"],
            location_name=demo_loc["location_name"],
            latitude=demo_loc["latitude"],
            longitude=demo_loc["longitude"],
            created_at=history[0]["measured_at"] if history else None,
            latest_measured_at=latest["measured_at"] if latest else None,
            latest_measurements=snapshot,
            water_quality_status="DEMO_EVALUATION",
            status_reason="Synthetic demonstration dataset for UI testing and trend visualization",
            is_demo=True,
            recent_measurements=formatted_recent,
        )

    # 2. Check PostgreSQL database if identifier is numeric
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
    Retrieves chronological historical measurements for trend visualization.
    Returns 404 (None) if the location does not exist in demo or production databases.
    """
    clean_id = str(location_id).strip()

    # 1. Check demonstration stations
    demo_loc = get_demo_location_by_id(clean_id)
    if demo_loc:
        obs_list = get_demo_location_history(
            location_id=demo_loc["location_id"],
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        if obs_list is None:
            return None

        records = [
            LocationHistoryItem(
                id=obs["id"],
                water_body_id=demo_loc["location_id"],
                location_id=demo_loc["location_id"],
                measured_at=obs["measured_at"],
                ph=obs.get("ph"),
                dissolved_oxygen=obs.get("dissolved_oxygen"),
                bod=obs.get("bod"),
                turbidity=obs.get("turbidity"),
                tds=obs.get("tds"),
                electrical_conductivity=obs.get("electrical_conductivity"),
                nitrate=obs.get("nitrate"),
                temperature=obs.get("temperature"),
                is_demo=True,
            )
            for obs in obs_list
        ]

        return LocationHistoryResponse(
            location_id=demo_loc["location_id"],
            water_body_id=demo_loc["location_id"],
            name=demo_loc["name"],
            water_body_type=demo_loc["water_body_type"],
            location_name=demo_loc["location_name"],
            latitude=demo_loc["latitude"],
            longitude=demo_loc["longitude"],
            is_demo=True,
            total_records=len(records),
            records=records,
        )

    # 2. Check PostgreSQL database
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
            fecal_coliform=r.fecal_coliform,
            total_coliform=r.total_coliform,
            sample_name=r.sample_name,
            wqi_score=r.wqi_score,
            wqi_status=r.wqi_status,
            safety_classification=r.safety_classification,
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
        latest_wqi_status=latest_rec.wqi_status if latest_rec else None,
        latest_safety_classification=latest_rec.safety_classification if latest_rec else None,
        is_demo=False,
        total_records=len(records),
        records=records,
    )
