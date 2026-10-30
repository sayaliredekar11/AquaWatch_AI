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
from typing import Any, Dict, List, Optional, Union
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
    Authorized Laboratory Authority signup.
    Public registration can NEVER supply or override a role; role is assigned securely by the backend.
    """
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    invitation_token: Optional[str] = Field(None, description="Optional legacy invitation token (deprecated)")

    model_config = ConfigDict(extra="ignore")


class LabInvitationCreate(BaseModel):
    """Schema for generating a new invitation (by administrator or existing Lab Authority)."""
    email: Optional[EmailStr] = Field(None, description="Optional email restriction for this invitation")
    expires_in_hours: int = Field(48, ge=1, le=720, description="Invitation validity duration in hours (default 48)")


class LabInvitationResponse(BaseModel):
    """Response returned upon successful creation of an invitation token."""
    invitation_token: str
    email: Optional[str] = None
    expires_at: datetime
    message: str


class LabInvitationValidationResponse(BaseModel):
    """Response schema for checking the validity of an invitation token."""
    valid: bool
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: str


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
    district: Optional[str] = Field(None, max_length=100, description="District name (e.g. Kolhapur, Sangli, Pune)")
    state: Optional[str] = Field(default="Maharashtra", max_length=100, description="State (default Maharashtra)")
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
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
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
    cod: Optional[float] = Field(None, ge=0.0, description="Chemical Oxygen Demand (mg/L)")
    ammonia_n: Optional[float] = Field(None, ge=0.0, description="Ammonia Nitrogen (mg/L)")
    chlorides: Optional[float] = Field(None, ge=0.0, description="Chlorides (mg/L)")
    sulphate: Optional[float] = Field(None, ge=0.0, description="Sulphate (mg/L)")
    fecal_coliform: Optional[float] = Field(None, ge=0.0, description="Fecal Coliform (MPN/100mL)")
    total_coliform: Optional[float] = Field(None, ge=0.0, description="Total Coliform (MPN/100mL)")
    sample_name: Optional[str] = Field(None, max_length=100, description="Sample label or identifier")
    wqi_score: Optional[float] = Field(None, description="Predicted numerical WQI score")
    wqi_prediction: Optional[str] = Field(None, description="Predicted WQI classification or score string")
    wqi_status: Optional[str] = Field(None, description="ML inference execution status")
    wqi_algorithm: Optional[str] = Field(None, description="Model algorithm used")
    safety_classification: Optional[str] = Field(None, description="Rule-based screening: SAFE, HARMFUL, or INCONCLUSIVE")
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
    cod: Optional[float] = Field(None, ge=0.0)
    ammonia_n: Optional[float] = Field(None, ge=0.0)
    chlorides: Optional[float] = Field(None, ge=0.0)
    sulphate: Optional[float] = Field(None, ge=0.0)
    fecal_coliform: Optional[float] = Field(None, ge=0.0)
    total_coliform: Optional[float] = Field(None, ge=0.0)
    sample_name: Optional[str] = Field(None, max_length=100)
    wqi_score: Optional[float] = None
    wqi_prediction: Optional[str] = None
    wqi_status: Optional[str] = None
    wqi_algorithm: Optional[str] = None
    safety_classification: Optional[str] = None
    measured_at: Optional[datetime] = None


class WaterQualityRecordResponse(WaterQualityRecordBase):
    """Response schema for returning water quality measurement details."""
    id: int
    water_body_id: int
    location_id: Optional[str] = None
    water_body_name: Optional[str] = None
    location_name: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
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
    cod: Optional[float] = Field(None, description="COD (mg/L)")
    ammonia_n: Optional[float] = Field(None, description="Ammonia Nitrogen (mg/L)")
    chlorides: Optional[float] = Field(None, description="Chlorides (mg/L)")
    sulphate: Optional[float] = Field(None, description="Sulphate (mg/L)")
    fecal_coliform: Optional[float] = Field(None, description="Fecal Coliform (MPN/100mL)")
    total_coliform: Optional[float] = Field(None, description="Total Coliform (MPN/100mL)")
    wqi_score: Optional[float] = Field(None, description="Calculated WQI Score")


class GISLocationMarker(BaseModel):
    """
    Map marker payload for GIS visualizations (Leaflet.js / OpenStreetMap).
    Guaranteed to include valid latitude and longitude coordinates.
    """
    water_body_id: Union[int, str]
    location_id: Optional[str] = None
    name: str
    water_body_type: str
    location_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: float
    longitude: float
    latest_measured_at: Optional[datetime] = None
    latest_measurements: Optional[MeasurementSnapshot] = None
    latest_wqi_score: Optional[float] = None
    latest_safety_classification: Optional[str] = None
    water_quality_status: str = Field("UNKNOWN", description="Current status indicator: UNKNOWN (pending standards)")
    status_reason: str = Field(..., description="Explanation of water quality status")
    is_demo: bool = Field(False, description="Whether this is an illustrative demonstration location")


class GISLocationDetail(BaseModel):
    """
    Detailed map marker inspection payload including measurement history.
    """
    water_body_id: Union[int, str]
    location_id: Optional[str] = None
    name: str
    water_body_type: str
    location_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: Optional[datetime] = None
    latest_measured_at: Optional[datetime] = None
    latest_measurements: Optional[MeasurementSnapshot] = None
    latest_wqi_score: Optional[float] = None
    latest_safety_classification: Optional[str] = None
    water_quality_status: str
    status_reason: str
    is_demo: bool = Field(False, description="Whether this is an illustrative demonstration location")
    recent_measurements: List[Any] = Field(default_factory=list)


class LocationHistoryItem(BaseModel):
    """Individual dated observation in water quality trend sequence."""
    id: Union[int, str]
    water_body_id: Optional[Union[int, str]] = None
    location_id: Optional[str] = None
    measured_at: datetime
    ph: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    bod: Optional[float] = None
    turbidity: Optional[float] = None
    tds: Optional[float] = None
    electrical_conductivity: Optional[float] = None
    nitrate: Optional[float] = None
    temperature: Optional[float] = None
    cod: Optional[float] = None
    ammonia_n: Optional[float] = None
    chlorides: Optional[float] = None
    sulphate: Optional[float] = None
    fecal_coliform: Optional[float] = None
    total_coliform: Optional[float] = None
    sample_name: Optional[str] = None
    wqi_score: Optional[float] = None
    wqi_status: Optional[str] = None
    safety_classification: Optional[str] = None
    is_demo: bool = False


class LocationHistoryResponse(BaseModel):
    """Location metadata paired with chronological historical observations."""
    location_id: str
    water_body_id: Union[int, str]
    name: str
    water_body_type: str
    location_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: float
    longitude: float
    latest_wqi_score: Optional[float] = None
    latest_wqi_status: Optional[str] = None
    latest_safety_classification: Optional[str] = None
    is_demo: bool = False
    total_records: int
    records: List[LocationHistoryItem] = Field(default_factory=list)


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
    """Input measurements required by the trained 12-feature WQI model."""

    dissolved_oxygen: float = Field(..., ge=0.0)
    ph: float = Field(..., ge=0.0, le=14.0)
    bod: float = Field(..., ge=0.0)
    cod: float = Field(..., ge=0.0)
    nitrate: float = Field(..., ge=0.0)
    ammonia_n: float = Field(..., ge=0.0)
    turbidity: float = Field(..., ge=0.0)
    tds: float = Field(..., ge=0.0)
    chlorides: float = Field(..., ge=0.0)
    sulphate: float = Field(..., ge=0.0)
    fecal_coliform: float = Field(..., ge=0.0)
    total_coliform: float = Field(..., ge=0.0)

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
    wqi_score: Optional[float] = Field(None, description="Exact numerical WQI score produced by the regression model")
    algorithm: Optional[str] = Field("Decision Tree Regressor", description="Machine learning algorithm name")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Prediction confidence score or probability (0.0 to 1.0)")
    model_version: Optional[str] = Field(None, description="Identifier of the model artifact or endpoint")
    features_used: Dict[str, Optional[float]] = Field(..., description="Copy of input features passed to the model")
    disclaimer: str = Field(
        "WQI is a statistical index calculated by a DecisionTreeRegressor model based on physical, chemical, and biological inputs. It does NOT constitute medical or certified drinking-water safety approval.",
        description="Scientific interpretation disclaimer",
    )


# ==========================================================
# Water Quality Sample Testing & Demo Schemas
# ==========================================================

class ParameterAssessment(BaseModel):
    """
    Detailed assessment of an individual water quality parameter against standard baseline.
    """
    parameter: str = Field(..., description="Parameter key (e.g. 'ph', 'dissolved_oxygen')")
    display_name: str = Field(..., description="Parameter display name (e.g. 'pH')")
    unit: str = Field(..., description="Measurement unit (e.g. 'mg/L')")
    value: Optional[float] = Field(None, description="Submitted measurement value")
    standard_range: str = Field(..., description="Configured acceptable standard range (e.g. '6.5 - 8.5')")
    status: str = Field(..., description="Parameter evaluation status: 'PASS', 'FAIL', or 'INSUFFICIENT'")
    message: str = Field(..., description="Detailed explanation of this parameter's assessment")


class WaterQualityTestRequest(BaseModel):
    """
    Schema for validating and testing arbitrary water quality measurement samples.
    Supports predefined dummy samples and laboratory test inputs.
    Parameters are optional to allow evaluating incomplete samples as INCONCLUSIVE.
    """
    sample_name: str = Field(default="Custom Sample", min_length=1, max_length=100, description="Identifier or name of sample")
    is_demo: bool = Field(default=True, description="Flag indicating if the sample is an illustrative test input")
    ph: Optional[float] = Field(None, description="pH value (acceptable range: 6.5 to 8.5)")
    dissolved_oxygen: Optional[float] = Field(None, description="Dissolved Oxygen in mg/L (acceptable: >= 4.0 mg/L)")
    bod: Optional[float] = Field(None, description="Biochemical Oxygen Demand in mg/L (acceptable: <= 3.0 mg/L)")
    turbidity: Optional[float] = Field(None, description="Turbidity in NTU (acceptable: <= 5.0 NTU)")
    tds: Optional[float] = Field(None, description="Total Dissolved Solids in mg/L (acceptable: <= 500.0 mg/L)")
    electrical_conductivity: Optional[float] = Field(None, description="Electrical Conductivity in µS/cm")
    nitrate: Optional[float] = Field(None, description="Nitrate in mg/L")
    temperature: Optional[float] = Field(None, description="Water temperature in °C")
    cod: Optional[float] = Field(None, ge=0.0, description="Chemical Oxygen Demand in mg/L")
    ammonia_n: Optional[float] = Field(None, ge=0.0, description="Ammonia Nitrogen in mg/L")
    chlorides: Optional[float] = Field(None, ge=0.0, description="Chlorides in mg/L")
    sulphate: Optional[float] = Field(None, ge=0.0, description="Sulphate in mg/L")
    fecal_coliform: Optional[float] = Field(None, ge=0.0, description="Fecal Coliform in MPN/100mL")
    total_coliform: Optional[float] = Field(None, ge=0.0, description="Total Coliform in MPN/100mL")
    location_id: Optional[int] = Field(default=None, description="Database ID of the monitored location")
    water_body_id: Optional[int] = Field(default=None, description="Target water body ID (synonym for location_id)")
    sampled_at: Optional[datetime] = Field(default=None, description="Timestamp when sample was collected")
    save_to_db: bool = Field(default=True, description="Persist this record to PostgreSQL database")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sample_name": "Sample A",
                "is_demo": True,
                "ph": 7.2,
                "dissolved_oxygen": 7.0,
                "bod": 2.0,
                "turbidity": 3.0,
                "tds": 250.0,
                "electrical_conductivity": 320.0,
                "nitrate": 1.2,
                "temperature": 22.0,
                "cod": 10.0,
                "ammonia_n": 0.2,
                "chlorides": 25.0,
                "sulphate": 30.0,
                "fecal_coliform": 20.0,
                "total_coliform": 50.0,
                "save_to_db": False,
            }
        }
    )


class WaterQualityTestResponse(BaseModel):
    """
    Structured response returned when evaluating a water quality test sample.
    Includes rule-based safety classification: SAFE, HARMFUL, or INCONCLUSIVE.
    """
    status: str = Field(default="SUCCESS", description="Evaluation status (e.g. SUCCESS)")
    classification: str = Field(..., description="Safety classification: SAFE, HARMFUL, or INCONCLUSIVE")
    result_type: str = Field(default="DEMO_RULE_BASED", description="Assessment type: DEMO_RULE_BASED")
    sample_name: str = Field(..., description="Name or identifier of tested sample")
    is_demo: bool = Field(default=True, description="True if marked as demo data")
    standard_name: str = Field(..., description="Name of the standard baseline evaluated against")
    standard_intended_use: str = Field(..., description="Intended water use category for the standard")
    parameters_received: Dict[str, Optional[float]] = Field(..., description="Submitted measurements")
    parameter_assessments: List[ParameterAssessment] = Field(default_factory=list, description="Parameter-by-parameter assessments")
    failed_parameters: List[str] = Field(default_factory=list, description="Parameters that failed criteria")
    passed_parameters: List[str] = Field(default_factory=list, description="Parameters that passed criteria")
    reasons: List[str] = Field(default_factory=list, description="Reasons explaining the classification decision")
    warnings: List[str] = Field(default_factory=list, description="Boundary or caution warnings")
    limitations: str = Field(..., description="Scientific limitations of this 5-parameter screening")
    evaluated_at: datetime = Field(..., description="Server timestamp of evaluation")
    sampled_at: Optional[datetime] = Field(default=None, description="Sample collection timestamp")
    persisted_to_database: bool = Field(default=False, description="Whether this sample was saved into PostgreSQL")
    persisted_record_id: Optional[int] = Field(default=None, description="PostgreSQL record ID if saved")
    location_id: Optional[str] = Field(default=None, description="Monitored location ID")
    water_body_id: Optional[int] = Field(default=None, description="Monitored water body ID")
    location_name: Optional[str] = Field(default=None, description="Geographical location description")
    water_body_name: Optional[str] = Field(default=None, description="Name of the water body")
    district: Optional[str] = Field(default=None, description="District name")
    state: Optional[str] = Field(default=None, description="State name")
    ml_model_status: str = Field(default="UNAVAILABLE", description="Status of ML model deployment")
    ml_model_details: str = Field(..., description="Explanation regarding ML model integration")
    ml_prediction: Optional[PredictionResponse] = Field(None, description="Trained ML model WQI prediction output when all 12 features are supplied")
    wqi_score: Optional[float] = Field(default=None, description="Predicted numerical WQI score")
    message: str = Field(..., description="Human-readable server summary")




class PlaceSearchResult(BaseModel):
    """
    Search result for geocoded location within Maharashtra.
    """
    place_id: Union[str, int]
    name: str
    display_name: str
    lat: float
    lon: float
    type: Optional[str] = "location"
    is_maharashtra: bool = True
