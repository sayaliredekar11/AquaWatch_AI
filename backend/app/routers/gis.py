"""
AquaWatch AI - GIS & Mapping Router

Provides map marker and location data for Leaflet.js / OpenStreetMap frontend integration.

Endpoints:
- GET /gis/locations                    : Public map markers with valid coordinates and latest measurements
- GET /gis/locations/{location_id}       : Detailed marker view with latest snapshot & recent records
- GET /gis/locations/{location_id}/history: Chronological trend data sequence for Recharts visualization
"""

from datetime import datetime
import json
import urllib.request
import urllib.parse
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GISLocationDetail, GISLocationMarker, LocationHistoryResponse, PlaceSearchResult
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


# ==========================================================
# 4. Search Places in Maharashtra (Geocoding Proxy & Cache)
# ==========================================================

_SEARCH_CACHE: dict = {}

MAHARASHTRA_FALLBACK_PLACES = [
    {
        "place_id": "fallback_sangli",
        "name": "Sangli",
        "display_name": "Sangli, Miraj, Sangli District, Maharashtra, 416416, India",
        "lat": 16.8502534,
        "lon": 74.5948885,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_pune",
        "name": "Pune",
        "display_name": "Pune, Pune City Subdistrict, Pune District, Maharashtra, 411001, India",
        "lat": 18.5213738,
        "lon": 73.8545071,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_nashik",
        "name": "Nashik",
        "display_name": "Nashik, Nashik Subdistrict, Nashik District, Maharashtra, 422001, India",
        "lat": 20.0112475,
        "lon": 73.7902364,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_kolhapur",
        "name": "Kolhapur",
        "display_name": "Kolhapur, Karvir, Kolhapur District, Maharashtra, 416003, India",
        "lat": 16.7028412,
        "lon": 74.2405329,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_godavari",
        "name": "Godavari River",
        "display_name": "Godavari River, Trimbak, Nashik District, Maharashtra, India",
        "lat": 19.9253576,
        "lon": 73.5265365,
        "type": "river",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_krishna",
        "name": "Krishna River",
        "display_name": "Krishna River, Sangli Basin, Maharashtra, India",
        "lat": 16.8524,
        "lon": 74.5815,
        "type": "river",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_panchganga",
        "name": "Panchganga River",
        "display_name": "Panchganga River, Shiroli Basin, Kolhapur District, Maharashtra, India",
        "lat": 16.7128,
        "lon": 74.2384,
        "type": "river",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_mula_mutha",
        "name": "Mula-Mutha River",
        "display_name": "Mula-Mutha River, Bund Garden, Pune, Maharashtra, India",
        "lat": 18.5204,
        "lon": 73.8567,
        "type": "river",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_venna",
        "name": "Venna Lake",
        "display_name": "Venna Lake, Mahabaleshwar, Satara District, Maharashtra, India",
        "lat": 17.9237,
        "lon": 73.6586,
        "type": "lake",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_mumbai",
        "name": "Mumbai",
        "display_name": "Mumbai, Mumbai Suburban, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_nagpur",
        "name": "Nagpur",
        "display_name": "Nagpur, Nagpur District, Maharashtra, India",
        "lat": 21.1458,
        "lon": 79.0882,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_satara",
        "name": "Satara",
        "display_name": "Satara, Satara District, Maharashtra, India",
        "lat": 17.6805,
        "lon": 73.9997,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_aurangabad",
        "name": "Chhatrapati Sambhajinagar",
        "display_name": "Chhatrapati Sambhajinagar (Aurangabad), Maharashtra, India",
        "lat": 19.8762,
        "lon": 75.3433,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_solapur",
        "name": "Solapur",
        "display_name": "Solapur, Solapur District, Maharashtra, India",
        "lat": 17.6599,
        "lon": 75.9064,
        "type": "city",
        "is_maharashtra": True,
    },
    {
        "place_id": "fallback_thane",
        "name": "Thane",
        "display_name": "Thane, Thane District, Maharashtra, India",
        "lat": 19.2183,
        "lon": 72.9781,
        "type": "city",
        "is_maharashtra": True,
    },
]


@router.get(
    "/search",
    response_model=List[PlaceSearchResult],
    summary="Search places, water bodies, and locations in Maharashtra",
)
def search_maharashtra_places(
    q: str = Query(..., min_length=2, description="Place or water body name in Maharashtra"),
):
    """
    Searches places, towns, cities, and water bodies restricted to Maharashtra, India.
    - Uses OpenStreetMap Nominatim geocoding bounded to Maharashtra.
    - Caches results to respect Nominatim usage policy (1 request/sec limit).
    - Filters out any coordinates that lie outside Maharashtra.
    - Includes robust fallback to ensure high reliability even in offline / sandboxed environments.
    """
    clean_q = q.strip()
    cache_key = clean_q.lower()

    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    results: List[dict] = []

    # 1. Try querying OpenStreetMap Nominatim geocoding service
    try:
        params = {
            "q": clean_q,
            "format": "json",
            "addressdetails": "1",
            "countrycodes": "in",
            "viewbox": "72.5,22.2,80.9,15.6",
            "bounded": "1",
            "limit": "8",
        }
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AquaWatch-AI/1.0 (contact@aquawatch.ai; water-quality-map)"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                try:
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    # Restrict to Maharashtra coordinates
                    if 15.5 <= lat <= 22.2 and 72.5 <= lon <= 81.0:
                        state = item.get("address", {}).get("state", "").lower()
                        display = item.get("display_name", "").lower()
                        if "maharashtra" in state or "maharashtra" in display or not state:
                            results.append({
                                "place_id": str(item.get("place_id", len(results) + 1)),
                                "name": item.get("name") or item.get("display_name", "").split(",")[0].strip(),
                                "display_name": item.get("display_name", ""),
                                "lat": lat,
                                "lon": lon,
                                "type": item.get("type", "location"),
                                "is_maharashtra": True,
                            })
                except Exception:
                    continue
    except Exception:
        # Network error or timeout; fallback to local Maharashtra dataset
        pass

    # 2. Check fallback Maharashtra locations if Nominatim had no matches or failed
    if not results:
        q_clean = clean_q.lower()
        q_tokens = [t.strip() for t in q_clean.replace(",", " ").replace("-", " ").split() if len(t.strip()) > 1]
        for p in MAHARASHTRA_FALLBACK_PLACES:
            target_text = f"{p['name']} {p['display_name']} {p['type']}".lower()
            if q_clean in target_text or (q_tokens and all(tok in target_text for tok in q_tokens)):
                results.append(p)

    # Cache result
    if results:
        _SEARCH_CACHE[cache_key] = results

    return results
