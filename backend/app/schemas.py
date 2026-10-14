"""
AquaWatch AI - Pydantic Data Schemas

Pydantic schemas validate request payloads, ensure data integrity,
and serialize safe response bodies without leaking passwords or sensitive secrets.

Day 1: Root & Health Schemas
Day 2: Authentication & Authorization Schemas
Day 3: Water Body & Water Quality Measurement CRUD Schemas
Day 5: GIS Mapping & Dashboard Analytics Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import UserRole


# ==========================================================
# Day 1 Foundation Schemas
# ==========================================================

class MessageResponse(BaseModel):
    """Response schema for general root/information endpoints."""
    message: str


class HealthResponse(BaseModel):
    """Response schema for the basic service health check endpoint."""
    status: str


class DbHealthResponse(BaseModel):
    """Response schema for the database connectivity health check."""
    status: str
    database: str


# ==========================================================
# Day 2 Authentication & Authorization Schemas
# ==========================================================

class UserRegisterRequest(BaseModel):
    """
    Schema for user registration.
    Only accepts name, email, and password.
    Public registration can NEVER supply a role; role is assigned securely by the backend.
    """
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")

    model_config = ConfigDict(extra="ignore")


class UserResponse(BaseModel):
    """
    Safe public response schema for user details.
    Never exposes passwords or password hashes.
    """
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """
    Schema for successful authentication response.
    Returns standard Bearer access token and lifetime in seconds.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration duration in seconds")


class RoleTestResponse(BaseModel):
    """
    Schema for role-based authorization test endpoints.
    """
    message: str
    user_email: str
    role: UserRole


# ==========================================================
# Day 3 Water Body Schemas
# ==========================================================

class WaterBodyBase(BaseModel):
    """Common fields for Water Body entities."""
    name: str = Field(..., min_length=2, max_length=100, description="Water body name (e.g. Ganges, Dal Lake)")
    water_body_type: str = Field(..., min_length=2, max_length=50, description="Type: river, lake, reservoir, canal")
    location_name: str = Field(..., min_length=2, max_length=200, description="Location description or region")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Geographic latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Geographic longitude (-180 to 180)")


class WaterBodyCreate(WaterBodyBase):
    """Schema for creating a new monitored water body."""
    pass


class WaterBodyUpdate(BaseModel):
    """Schema for updating a water body via PATCH (all fields optional)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    water_body_type: Optional[str] = Field(None, min_length=2, max_length=50)
    location_name: Optional[str] = Field(None, min_length=2, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class WaterBodyResponse(WaterBodyBase):
    """Response schema for returning water body details."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Day 3 Water Quality Measurement Schemas
# ==========================================================

class WaterQualityRecordBase(BaseModel):
    """
    Common fields and validation for water quality parameter measurements.
    Documented units:
    - ph: 0.0 - 14.0 (dimensionless)
    - dissolved_oxygen: mg/L (nonnegative)
    - bod: mg/L (nonnegative)
    - turbidity: NTU (nonnegative)
    - tds: mg/L (nonnegative)
    - electrical_conductivity: µS/cm (nonnegative)
    - nitrate: mg/L (nonnegative)
    - temperature: °C (-20.0 to 100.0)
    """
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="pH value (0.0 to 14.0)")
    dissolved_oxygen: Optional[float] = Field(None, ge=0.0, description="Dissolved Oxygen (mg/L)")
    bod: Optional[float] = Field(None, ge=0.0, description="Biochemical Oxygen Demand (mg/L)")
    turbidity: Optional[float] = Field(None, ge=0.0, description="Turbidity (NTU)")
    tds: Optional[float] = Field(None, ge=0.0, description="Total Dissolved Solids (mg/L)")
    electrical_conductivity: Optional[float] = Field(None, ge=0.0, description="Electrical Conductivity (µS/cm)")
    nitrate: Optional[float] = Field(None, ge=0.0, description="Nitrate concentration (mg/L)")
    temperature: Optional[float] = Field(None, ge=-20.0, le=100.0, description="Water temperature in °C")
    measured_at: datetime = Field(..., description="Timestamp of sampling/measurement")


class WaterQualityRecordCreate(WaterQualityRecordBase):
    """Schema for logging a new water quality measurement."""
    water_body_id: int = Field(..., gt=0, description="Foreign key ID of the monitored water body")


class WaterQualityRecordUpdate(BaseModel):
    """Schema for partially updating a water quality measurement (all fields optional)."""
    water_body_id: Optional[int] = Field(None, gt=0)
    ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    dissolved_oxygen: Optional[float] = Field(None, ge=0.0)
    bod: Optional[float] = Field(None, ge=0.0)
    turbidity: Optional[float] = Field(None, ge=0.0)
    tds: Optional[float] = Field(None, ge=0.0)
    electrical_conductivity: Optional[float] = Field(None, ge=0.0)
    nitrate: Optional[float] = Field(None, ge=0.0)
    temperature: Optional[float] = Field(None, ge=-20.0, le=100.0)
    measured_at: Optional[datetime] = None


class WaterQualityRecordResponse(WaterQualityRecordBase):
    """Response schema for returning water quality measurement details."""
    id: int
    water_body_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Day 5 GIS Mapping Schemas
# ==========================================================

class MeasurementSnapshot(BaseModel):
    """Compact summary of physical and chemical parameters."""
    ph: Optional[float] = Field(None, description="pH (dimensionless)")
    dissolved_oxygen: Optional[float] = Field(None, description="Dissolved Oxygen (mg/L)")
    bod: Optional[float] = Field(None, description="Biochemical Oxygen Demand (mg/L)")
    turbidity: Optional[float] = Field(None, description="Turbidity (NTU)")
    tds: Optional[float] = Field(None, description="Total Dissolved Solids (mg/L)")
    electrical_conductivity: Optional[float] = Field(None, description="Electrical Conductivity (µS/cm)")
    nitrate: Optional[float] = Field(None, description="Nitrate (mg/L)")
    temperature: Optional[float] = Field(None, description="Temperature (°C)")


class GISLocationMarker(BaseModel):
    """
    Map marker payload for GIS visualizations (Leaflet.js / OpenStreetMap).
    Guaranteed to include valid latitude and longitude coordinates.
    """
    water_body_id: int
    name: str
    water_body_type: str
    location_name: str
    latitude: float
    longitude: float
    latest_measured_at: Optional[datetime] = None
    latest_measurements: Optional[MeasurementSnapshot] = None
    water_quality_status: str = Field("UNKNOWN", description="Current status indicator: UNKNOWN (pending standards)")
    status_reason: str = Field(..., description="Explanation of water quality status")


class GISLocationDetail(BaseModel):
    """
    Detailed map marker inspection payload including measurement history.
    """
    water_body_id: int
    name: str
    water_body_type: str
    location_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    latest_measured_at: Optional[datetime] = None
    latest_measurements: Optional[MeasurementSnapshot] = None
    water_quality_status: str
    status_reason: str
    recent_measurements: List[WaterQualityRecordResponse] = Field(default_factory=list)


# ==========================================================
# Day 5 Dashboard Analytics Schemas
# ==========================================================

class DashboardSummaryResponse(BaseModel):
    """High-level system statistics for public dashboard view."""
    total_water_bodies: int = Field(..., description="Total monitored water bodies in database")
    mapped_locations: int = Field(..., description="Water bodies with valid map coordinates")
    total_measurements: int = Field(..., description="Total water quality measurement records")
    latest_measurement_timestamp: Optional[datetime] = Field(None, description="Most recent sampling timestamp")
    active_monitoring_locations: int = Field(..., description="Count of distinct locations with recorded measurements")


class ParameterStatistic(BaseModel):
    """Aggregated statistic for a single parameter with its unit."""
    value: Optional[float] = Field(None, description="Calculated average or null if no measurements exist")
    unit: str = Field(..., description="Measurement unit of parameter")


class WaterQualityOverviewResponse(BaseModel):
    """Statistical overview of water quality parameters computed using SQL aggregation."""
    total_records_analyzed: int
    latest_measurement_timestamp: Optional[datetime]
    average_ph: ParameterStatistic
    average_dissolved_oxygen: ParameterStatistic
    average_bod: ParameterStatistic
    average_turbidity: ParameterStatistic
    average_tds: ParameterStatistic
    average_electrical_conductivity: ParameterStatistic
    average_nitrate: ParameterStatistic
    average_temperature: ParameterStatistic


class RecentMeasurementItem(BaseModel):
    """Recent measurement log entry joined with location context."""
    id: int
    water_body_id: int
    water_body_name: str
    water_body_type: str
    location_name: str
    ph: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    bod: Optional[float] = None
    turbidity: Optional[float] = None
    tds: Optional[float] = None
    electrical_conductivity: Optional[float] = None
    nitrate: Optional[float] = None
    temperature: Optional[float] = None
    measured_at: datetime
    created_at: datetime


class OfficialDashboardSummaryResponse(BaseModel):
    """Authorized dashboard statistics for regulatory and lab authorities."""
    public_summary: DashboardSummaryResponse
    unmonitored_water_bodies_count: int
    measurements_last_7_days: int
    measurements_last_30_days: int
    total_registered_users: int
    users_by_role: Dict[str, int]


# ==========================================================
# Day 4 Machine Learning Prediction Schemas
# ==========================================================

class PredictionInput(BaseModel):
    """
    Input feature vector for water quality ML prediction.
    Features map directly to chemical and physical parameters monitored in Day 3.
    """
    ph: float = Field(..., ge=0.0, le=14.0, description="pH value (0.0 to 14.0)")
    dissolved_oxygen: float = Field(..., ge=0.0, description="Dissolved Oxygen (mg/L)")
    bod: float = Field(..., ge=0.0, description="Biochemical Oxygen Demand (mg/L)")
    turbidity: float = Field(..., ge=0.0, description="Turbidity (NTU)")
    tds: float = Field(..., ge=0.0, description="Total Dissolved Solids (mg/L)")
    electrical_conductivity: Optional[float] = Field(None, ge=0.0, description="Electrical Conductivity (µS/cm)")
    nitrate: Optional[float] = Field(None, ge=0.0, description="Nitrate (mg/L)")
    temperature: Optional[float] = Field(None, ge=-20.0, le=100.0, description="Water temperature (°C)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ph": 7.4,
                "dissolved_oxygen": 6.8,
                "bod": 2.1,
                "turbidity": 4.5,
                "tds": 240.0,
                "electrical_conductivity": 350.0,
                "nitrate": 1.2,
                "temperature": 21.5,
            }
        }
    )


class PredictionResponse(BaseModel):
    """
    Standard output contract returned when the ML model completes inference.
    """
    status: str = Field(..., description="Inference status: SUCCESS or MOCK")
    prediction: str = Field(..., description="Predicted water quality classification / pollution risk category")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Prediction confidence score or probability (0.0 to 1.0)")
    model_version: Optional[str] = Field(None, description="Identifier of the model artifact or endpoint")
    features_used: Dict[str, Optional[float]] = Field(..., description="Copy of input features passed to the model")
