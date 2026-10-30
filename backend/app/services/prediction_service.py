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
        self._model_cache = None
        self._cached_path = None
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

    def _resolve_model_path(self) -> str:
        """Finds the model artifact path relative to current working directory or backend root."""
        candidates = [
            self.model_path,
            os.path.join(os.path.dirname(__file__), "..", "..", self.model_path),
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "AquaWatchAI_Best_Model.joblib"),
            os.path.join(os.getcwd(), self.model_path),
            os.path.join(os.getcwd(), "backend", self.model_path),
            os.path.join(os.getcwd(), "backend", "models", "AquaWatchAI_Best_Model.joblib"),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return os.path.abspath(p)
        return self.model_path

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
        ph = features.get("ph", 7.0)
        do = features.get("dissolved_oxygen", 6.0)
        is_favorable = (6.5 <= ph <= 8.5) and (do >= 5.0)

        prediction_label = "POTABLE" if is_favorable else "NON_POTABLE"
        confidence = 0.91 if is_favorable else 0.85

        return PredictionResponse(
            status="MOCK",
            prediction=prediction_label,
            wqi_score=45.0 if is_favorable else 85.0,
            algorithm="Mock Predictor",
            confidence=confidence,
            model_version="mock-test-v1.0",
            features_used=features,
            disclaimer="Mock prediction strictly for testing.",
        )

    async def _execute_local_model(self, features: Dict[str, Any]) -> PredictionResponse:
        """Load the saved model artifact and predict WQI using all 12 features."""
        resolved_path = self._resolve_model_path()
        if not os.path.exists(resolved_path):
            raise MLServiceUnavailableException(
                f"Model file not found at '{self.model_path}' (resolved: '{resolved_path}')"
            )

        try:
            import joblib
            import pandas as pd

            if self._model_cache is None or self._cached_path != resolved_path:
                artifact = joblib.load(resolved_path)
                self._model_cache = artifact
                self._cached_path = resolved_path
            else:
                artifact = self._model_cache

            if not isinstance(artifact, dict) or "model" not in artifact:
                raise ValueError(
                    "Expected a model artifact dictionary containing 'model' and 'features'."
                )

            model = artifact["model"]
            model_features = artifact.get("features")

            if not model_features or len(model_features) != 12:
                raise ValueError(
                    "The saved model must contain the exact 12-feature list."
                )

            feature_mapping = {
                "Dissolved O2": "dissolved_oxygen",
                "pH": "ph",
                "BOD": "bod",
                "COD": "cod",
                "Nitrate N": "nitrate",
                "Amonia N": "ammonia_n",
                "Turbidity": "turbidity",
                "Total Dissolved Solids": "tds",
                "Chlorides": "chlorides",
                "Sulphate": "sulphate",
                "Fecal Coliform": "fecal_coliform",
                "Total Coliform": "total_coliform",
            }

            missing = [
                feature_mapping[name]
                for name in model_features
                if name not in feature_mapping
                or feature_mapping[name] not in features
                or features[feature_mapping[name]] is None
            ]

            if missing:
                raise ValueError(
                    "Missing required model measurements: " + ", ".join(missing)
                )

            # Construct DataFrame with exact feature names to eliminate scikit-learn warnings
            row_dict = {
                name: float(features[feature_mapping[name]])
                for name in model_features
            }
            df = pd.DataFrame([row_dict], columns=model_features)

            raw_pred = model.predict(df)
            wqi_score = round(float(raw_pred[0]), 2)
            algo_name = artifact.get("algorithm", "Decision Tree Regressor")

            return PredictionResponse(
                status="SUCCESS",
                prediction=f"{wqi_score:.2f}",
                wqi_score=wqi_score,
                algorithm=algo_name,
                confidence=None,
                model_version=f"local-{os.path.basename(resolved_path)}",
                features_used={
                    feature_mapping[name]: float(features[feature_mapping[name]])
                    for name in model_features
                },
                disclaimer=(
                    "WQI is a statistical index calculated by a DecisionTreeRegressor model based on physical, "
                    "chemical, and biological inputs. It does NOT constitute medical or certified drinking-water safety approval."
                ),
            )

        except Exception as e:
            raise MLServiceIntegrationException(
                f"Local model prediction failed: {str(e)}"
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
            prediction = data.get("prediction")
            if not prediction:
                raise ValueError("Response missing required 'prediction' key.")

            wqi_score = data.get("wqi_score")
            if wqi_score is None:
                try:
                    wqi_score = float(prediction)
                except (ValueError, TypeError):
                    wqi_score = None

            return PredictionResponse(
                status="SUCCESS",
                prediction=str(prediction),
                wqi_score=wqi_score,
                algorithm=data.get("algorithm", "Remote ML Service"),
                confidence=data.get("confidence"),
                model_version=data.get("model_version", "remote-api"),
                features_used=features,
                disclaimer=data.get(
                    "disclaimer",
                    "WQI is a statistical index calculated based on physical, chemical, and biological inputs. It does NOT constitute medical or certified drinking-water safety approval."
                ),
            )
        except Exception as e:
            raise MLServiceIntegrationException(
                f"Failed to parse ML microservice response: {str(e)}"
            )


# Singleton instance for application dependency injection
prediction_service = PredictionService()
