"""
AquaWatch AI - Machine Learning Prediction Service

Isolates model communication and inference execution from FastAPI route handlers.

Integration Modes (Configured via ML_INTEGRATION_MODE in .env):
1. 'none'  : Default normal operating mode when the ML model has not yet been deployed.
             Safely raises MLServiceUnavailableException (HTTP 503).
             NEVER produces fake predictions.
2. 'file'  : Option A - Local trained artifact (e.g., model.joblib or model.pkl).
3. 'api'   : Option B - Separate ML microservice endpoint (via HTTP POST).

Testing / Development Flag:
- ML_MOCK_MODE=true : Enables a clearly labeled mock prediction for automated tests
                      and offline API contract verification.
"""

import os
from typing import Any, Dict, Optional
import httpx
from dotenv import load_dotenv

from app.schemas import PredictionInput, PredictionResponse

load_dotenv()


class MLServiceException(Exception):
    """Base exception for ML prediction service errors."""
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MLServiceUnavailableException(MLServiceException):
    """Raised when the ML model artifact or external microservice is not configured/available."""
    def __init__(self, message: str = "ML prediction service is currently unavailable. Model integration is pending deployment."):
        super().__init__(message, status_code=503)


class MLServiceTimeoutException(MLServiceException):
    """Raised when the external ML microservice times out."""
    def __init__(self, message: str = "The ML prediction microservice timed out."):
        super().__init__(message, status_code=504)


class MLServiceIntegrationException(MLServiceException):
    """Raised when the external ML microservice returns an invalid response."""
    def __init__(self, message: str = "The ML prediction service returned an invalid response."):
        super().__init__(message, status_code=502)


class PredictionService:
    """
    Service layer coordinating inference requests between the backend API
    and the Machine Learning model integration.
    """

    def __init__(self):
        self._refresh_config()

    def _refresh_config(self):
        """Loads latest environment configuration settings."""
        self.mode = os.getenv("ML_INTEGRATION_MODE", "none").strip().lower()
        self.model_path = os.getenv("ML_MODEL_PATH", "models/water_quality_model.joblib")
        self.service_url = os.getenv("ML_SERVICE_URL", "http://localhost:8501/predict")
        try:
            self.timeout = float(os.getenv("ML_SERVICE_TIMEOUT_SECONDS", "5.0"))
        except ValueError:
            self.timeout = 5.0
        self.mock_mode = os.getenv("ML_MOCK_MODE", "false").strip().lower() in ("true", "1", "yes")

    async def predict(self, input_data: PredictionInput) -> PredictionResponse:
        """
        Executes inference for the provided water quality measurement features.
        """
        self._refresh_config()
        features = input_data.model_dump()

        # 1. Mock Mode (strictly for automated testing or explicit local development)
        if self.mock_mode:
            return self._execute_mock(features)

        # 2. Mode 'none': Model pending delivery from ML teammate
        if self.mode == "none":
            raise MLServiceUnavailableException(
                "Machine learning prediction model is currently unavailable (not configured or deployed). "
                "Backend is awaiting model artifact (Option A) or ML microservice endpoint (Option B) from ML teammate."
            )

        # 3. Mode 'file': Option A - Local trained artifact (.joblib or .pkl)
        elif self.mode == "file":
            return await self._execute_local_model(features)

        # 4. Mode 'api': Option B - External ML microservice endpoint
        elif self.mode == "api":
            return await self._execute_remote_api(features)

        else:
            raise MLServiceUnavailableException(
                f"Unknown ML_INTEGRATION_MODE '{self.mode}'. Supported modes are 'none', 'file', or 'api'."
            )

    def _execute_mock(self, features: Dict[str, Any]) -> PredictionResponse:
        """
        Generates a clearly labeled mock prediction for testing purposes only.
        """
        # Determine a mock status for testing verification based on pH and DO
        ph = features.get("ph", 7.0)
        do = features.get("dissolved_oxygen", 6.0)
        is_favorable = (6.5 <= ph <= 8.5) and (do >= 5.0)

        prediction_label = "POTABLE" if is_favorable else "NON_POTABLE"
        confidence = 0.91 if is_favorable else 0.85

        return PredictionResponse(
            status="MOCK",
            prediction=prediction_label,
            confidence=confidence,
            model_version="mock-test-v1.0",
            features_used=features,
        )

    async def _execute_local_model(self, features: Dict[str, Any]) -> PredictionResponse:
        """
        Loads and executes a local model artifact (Option A).
        """
        if not os.path.exists(self.model_path):
            raise MLServiceUnavailableException(
                f"Local model artifact file not found at path '{self.model_path}'. "
                "Please ensure the trained model artifact has been placed in the configured location."
            )

        try:
            # Dynamically attempt joblib or pickle loading
            import joblib  # type: ignore
            model = joblib.load(self.model_path)
        except ImportError:
            try:
                import pickle
                with open(self.model_path, "rb") as f:
                    model = pickle.load(f)
            except Exception as e:
                raise MLServiceIntegrationException(
                    f"Failed to load local model artifact: {str(e)}"
                )
        except Exception as e:
            raise MLServiceIntegrationException(
                f"Error initializing model artifact: {str(e)}"
            )

        try:
            # Documented input structure: list of values ordered by features
            # Can be adapted once teammate confirms feature ordering or DataFrame expectation
            feature_vector = [
                features.get("ph"),
                features.get("dissolved_oxygen"),
                features.get("bod"),
                features.get("turbidity"),
                features.get("tds"),
                features.get("electrical_conductivity", 0.0),
                features.get("nitrate", 0.0),
                features.get("temperature", 20.0),
            ]

            raw_pred = model.predict([feature_vector])
            prediction_label = str(raw_pred[0])

            confidence: Optional[float] = None
            if hasattr(model, "predict_proba"):
                probas = model.predict_proba([feature_vector])
                confidence = float(max(probas[0]))

            return PredictionResponse(
                status="SUCCESS",
                prediction=prediction_label,
                confidence=confidence,
                model_version=f"local-{os.path.basename(self.model_path)}",
                features_used=features,
            )
        except Exception as e:
            raise MLServiceIntegrationException(
                f"Inference execution failed on local model: {str(e)}"
            )

    async def _execute_remote_api(self, features: Dict[str, Any]) -> PredictionResponse:
        """
        Sends prediction request to an external ML microservice endpoint (Option B).
        """
        if not self.service_url:
            raise MLServiceUnavailableException("External ML service URL is not configured.")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.service_url, json=features)
            except httpx.TimeoutException:
                raise MLServiceTimeoutException(
                    f"ML service at '{self.service_url}' timed out after {self.timeout} seconds."
                )
            except (httpx.ConnectError, httpx.RequestError) as e:
                raise MLServiceUnavailableException(
                    f"Could not connect to external ML microservice at '{self.service_url}': {str(e)}"
                )

        if response.status_code != 200:
            raise MLServiceIntegrationException(
                f"External ML service responded with HTTP status {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            # Standard expected format from external service:
            # {"prediction": "...", "confidence": 0.85, "model_version": "..."}
            prediction = data.get("prediction")
            if not prediction:
                raise ValueError("Response missing required 'prediction' key.")

            return PredictionResponse(
                status="SUCCESS",
                prediction=str(prediction),
                confidence=data.get("confidence"),
                model_version=data.get("model_version", "remote-api"),
                features_used=features,
            )
        except Exception as e:
            raise MLServiceIntegrationException(
                f"Failed to parse ML microservice response: {str(e)}"
            )


# Singleton instance for application dependency injection
prediction_service = PredictionService()
