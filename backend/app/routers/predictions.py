"""
AquaWatch AI - Machine Learning Prediction Router

Provides API endpoints to request water quality pollution & potability predictions:
- POST /predictions/predict        : Run inference on provided measurement parameters
- GET  /predictions/record/{id}    : Run inference directly on an existing stored database record

Role-Based Access:
- Protected: LAB_AUTHORITY
- Unauthenticated requests receive HTTP 401
- Insufficient roles (e.g. NORMAL_USER) receive HTTP 403
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, WaterQualityRecord
from app.schemas import PredictionInput, PredictionResponse
from app.security import require_roles
from app.services.prediction_service import (
    MLServiceException,
    prediction_service,
)

router = APIRouter(prefix="/predictions", tags=["Machine Learning Predictions"])


# ==========================================================
# 1. POST /predictions/predict - Predict from Input Payload
# ==========================================================
@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict water quality status from input parameters",
)
async def predict_water_quality(
    payload: PredictionInput,
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Submits water quality parameters to the configured ML integration:
    - Allowed roles: LAB_AUTHORITY
    - Validates inputs scientifically (pH 0-14, nonnegative values)
    - If model is unavailable, returns HTTP 503 Service Unavailable
    - If external ML service times out, returns HTTP 504 Gateway Timeout
    - If in test/mock mode, returns a clearly labeled mock prediction
    """
    try:
        result = await prediction_service.predict(payload)
        return result
    except MLServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ==========================================================
# 2. GET /predictions/record/{record_id} - Predict from Stored Record
# ==========================================================
@router.get(
    "/record/{record_id}",
    response_model=PredictionResponse,
    summary="Predict water quality status from an existing database record",
)
async def predict_from_stored_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Fetches an existing measurement record from PostgreSQL and submits it for ML prediction:
    - Returns HTTP 404 if the record does not exist
    - Verifies that all 12 required model features are present (returns HTTP 400 if incomplete)
    - Does NOT modify the original record in the database
    - Does NOT create prediction history tables
    """
    record = db.query(WaterQualityRecord).filter(WaterQualityRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water quality measurement record with ID {record_id} not found.",
        )

    # Verify presence of all 12 model features
    required_features = [
        "dissolved_oxygen",
        "ph",
        "bod",
        "cod",
        "nitrate",
        "ammonia_n",
        "turbidity",
        "tds",
        "chlorides",
        "sulphate",
        "fecal_coliform",
        "total_coliform",
    ]
    missing = [feat for feat in required_features if getattr(record, feat) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Incomplete measurement record: Record #{record_id} is missing required ML model parameters: {missing}. "
                "The DecisionTreeRegressor model requires all 12 parameters to compute WQI."
            ),
        )

    # Construct validated prediction input from stored record
    prediction_input = PredictionInput(
        dissolved_oxygen=record.dissolved_oxygen,
        ph=record.ph,
        bod=record.bod,
        cod=record.cod,
        nitrate=record.nitrate,
        ammonia_n=record.ammonia_n,
        turbidity=record.turbidity,
        tds=record.tds,
        chlorides=record.chlorides,
        sulphate=record.sulphate,
        fecal_coliform=record.fecal_coliform,
        total_coliform=record.total_coliform,
    )

    try:
        result = await prediction_service.predict(prediction_input)
        return result
    except MLServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
