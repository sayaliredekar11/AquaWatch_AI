# AquaWatch AI — Backend

**Intelligent Water Quality Monitoring & Pollution Prediction Platform**

This repository contains the FastAPI backend for AquaWatch AI, using PostgreSQL, SQLAlchemy 2.x, Pydantic, Argon2 password hashing, PyJWT authentication, Role-Based Access Control (RBAC), and GIS & Dashboard analytics APIs.

---

## 1. Project Overview & Scope

AquaWatch AI provides real-time water quality monitoring, automated anomaly detection, and predictive pollution alerts.

> **Important Architecture Decisions:**
> 1. The **complaint management system** has been permanently removed from AquaWatch AI. No complaint-related tables, routes, or features exist in the system.
> 2. **Water quality classification:** In strict adherence to scientific integrity, status indicators for map markers return `UNKNOWN` pending adoption of approved regulatory standards (such as CPCB Designated Best Use criteria). We do not invent arbitrary thresholds or label water as safe for drinking without formal criteria.

---

## 2. Technology Stack

- **Language:** Python 3.10+ (tested on Python 3.14)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **Database:** [PostgreSQL](https://www.postgresql.org/)
- **ORM:** [SQLAlchemy 2.x](https://docs.sqlalchemy.org/en/20/)
- **Password Hashing:** `pwdlib` with `argon2`
- **Token Management:** `PyJWT`
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/)
- **Automated Testing:** `pytest` & `httpx` (FastAPI `TestClient`)

---

## 3. Folder Structure

```text
backend/
├── app/
│   ├── __init__.py          # Application package initializer
│   ├── main.py              # FastAPI app, CORS, lifespan, router inclusion
│   ├── database.py          # SQLAlchemy engine, session maker, get_db dependency
│   ├── models.py            # SQLAlchemy database models (User, WaterBody, WaterQualityRecord)
│   ├── schemas.py           # Pydantic schemas for requests, responses, GIS, and dashboards
│   ├── security.py          # Argon2 hashing, JWT management, RBAC dependencies
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # /auth: User registration, login, profile, role tests
│   │   ├── water_bodies.py  # /water-bodies: CRUD operations for water bodies
│   │   ├── water_quality.py # /water-quality: CRUD operations for measurements
│   │   ├── gis.py           # /gis: Map markers and detailed marker views
│   │   ├── dashboard.py     # /dashboard: Public and official aggregate analytics
│   │   └── predictions.py   # /predictions: ML prediction integration endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── water_quality_classifier.py # Status indicator classification service
│   │   ├── gis_service.py              # GIS query logic and marker assembly
│   │   ├── dashboard_service.py        # SQL aggregations and statistics
│   │   └── prediction_service.py       # ML model abstraction & microservice client
│   └── ml/
│       └── __init__.py      # Directory for ML teammate model artifacts
├── .env                     # Local environment secrets (IGNORED by git)
├── .env.example             # Template for environment variables
├── .gitignore               # Excludes venv, .env, and caches
├── requirements.txt         # Project dependencies
├── test_auth_flow.py        # Automated test suite for Day 2 Auth
├── test_day3_flow.py        # Automated test suite for Day 3 Water Quality CRUD
├── test_day4_flow.py        # Automated test suite for Day 4 ML Predictions
├── test_day5_flow.py        # Automated test suite for Day 5 GIS & Dashboards
└── README.md                # Comprehensive documentation
```

---

## 4. API Endpoints Reference

### General & Health Endpoints
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Public | Root welcome message |
| `GET` | `/health` | Public | Basic service liveness status |
| `GET` | `/health/db` | Public | PostgreSQL connectivity check (`SELECT 1`) |

### Authentication & Authorization Endpoints (`/auth`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Public | Register new citizen account (forces `CITIZEN` role) |
| `POST` | `/auth/login` | Public | OAuth2 form login, returns signed JWT Bearer token |
| `GET` | `/auth/me` | Authenticated | Profile details of currently logged-in user |
| `GET` | `/auth/test/citizen` | `CITIZEN` | Role-based test endpoint for citizens |
| `GET` | `/auth/test/lab` | `LAB_AUTHORITY` | Role-based test endpoint for lab authorities |
| `GET` | `/auth/test/official` | `POLLUTION_OFFICIAL` | Role-based test endpoint for pollution officials |
| `GET` | `/auth/test/admin` | `ADMIN` | Role-based test endpoint for system administrators |

### Water Body Management Endpoints (`/water-bodies`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/water-bodies` | `LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN` | Create a new monitored water body |
| `GET` | `/water-bodies` | All Authenticated | List all water bodies (supports `skip`, `limit`) |
| `GET` | `/water-bodies/{id}` | All Authenticated | Get water body details by ID |
| `PATCH` | `/water-bodies/{id}` | `LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN` | Partially update an existing water body |
| `DELETE` | `/water-bodies/{id}` | `ADMIN` only | Delete a water body (protected against silent data loss) |

### Water Quality Measurement Endpoints (`/water-quality`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/water-quality` | `LAB_AUTHORITY`, `ADMIN` | Log a new parameter measurement |
| `GET` | `/water-quality` | All Authenticated | List measurements with pagination and filters (`water_body_id`, date range) |
| `GET` | `/water-quality/{id}` | All Authenticated | Get measurement record details by ID |
| `PATCH` | `/water-quality/{id}` | `LAB_AUTHORITY`, `ADMIN` | Partially update an existing measurement |
| `DELETE` | `/water-quality/{id}` | `ADMIN` only | Delete a measurement record |

### GIS & Map Endpoints (`/gis`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/gis/locations` | Public | List map markers with coordinates and latest measurement |
| `GET` | `/gis/locations/{id}` | Public | Detailed marker inspection with recent measurement history |

### Dashboard Analytics Endpoints (`/dashboard`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/dashboard/summary` | Public | High-level platform totals (locations, mapped, total logs) |
| `GET` | `/dashboard/water-quality-overview` | Public | Statistical averages per parameter computed via SQL `AVG()` |
| `GET` | `/dashboard/recent-measurements` | Public | Recent measurement feed joined with location context |
| `GET` | `/dashboard/official-summary` | `LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN` | Administrative analytics and activity metrics |

### Machine Learning Prediction Endpoints (`/predictions`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/predictions/predict` | `LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN` | Run inference on provided water quality measurements |
| `GET` | `/predictions/record/{record_id}` | `LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN` | Run inference on an existing database record without mutating DB |

---

## 5. Documented Measurement Units & Parameter Validations

| Parameter | Column | Unit | Valid Range / Constraints |
| :--- | :--- | :--- | :--- |
| pH | `ph` | Dimensionless | `0.0` to `14.0` |
| Dissolved Oxygen | `dissolved_oxygen` | mg/L | Nonnegative (`>= 0.0`) |
| Biochemical Oxygen Demand | `bod` | mg/L | Nonnegative (`>= 0.0`) |
| Turbidity | `turbidity` | NTU | Nonnegative (`>= 0.0`) |
| Total Dissolved Solids | `tds` | mg/L | Nonnegative (`>= 0.0`) |
| Electrical Conductivity | `electrical_conductivity` | µS/cm | Nonnegative (`>= 0.0`) |
| Nitrate Concentration | `nitrate` | mg/L | Nonnegative (`>= 0.0`) |
| Water Temperature | `temperature` | °C | `-20.0` to `100.0` |

---

## 6. How to Run the Server

Open PowerShell in the `backend` directory:

```powershell
cd d:\AqauWatch_ai\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Interactive Swagger documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 7. Example Requests & Responses

### A. Get Map Markers (`GET /gis/locations`)
```json
[
  {
    "water_body_id": 1,
    "name": "Ganges River",
    "water_body_type": "river",
    "location_name": "Assi Ghat, Varanasi",
    "latitude": 25.2974,
    "longitude": 83.0064,
    "latest_measured_at": "2026-10-10T12:00:00Z",
    "latest_measurements": {
      "ph": 7.4,
      "dissolved_oxygen": 6.8,
      "bod": 2.1,
      "turbidity": 4.5,
      "tds": 240.0,
      "electrical_conductivity": 350.0,
      "nitrate": 1.2,
      "temperature": 21.5
    },
    "water_quality_status": "UNKNOWN",
    "status_reason": "Status pending adoption of approved regulatory water quality standards."
  }
]
```

### B. Public Dashboard Summary (`GET /dashboard/summary`)
```json
{
  "total_water_bodies": 12,
  "mapped_locations": 10,
  "total_measurements": 145,
  "latest_measurement_timestamp": "2026-10-10T12:00:00Z",
  "active_monitoring_locations": 8
}
```

### C. Parameter Overview (`GET /dashboard/water-quality-overview`)
```json
{
  "total_records_analyzed": 145,
  "latest_measurement_timestamp": "2026-10-10T12:00:00Z",
  "average_ph": { "value": 7.35, "unit": "dimensionless" },
  "average_dissolved_oxygen": { "value": 6.42, "unit": "mg/L" },
  "average_bod": { "value": 2.85, "unit": "mg/L" },
  "average_turbidity": { "value": 5.12, "unit": "NTU" },
  "average_tds": { "value": 235.40, "unit": "mg/L" },
  "average_electrical_conductivity": { "value": 348.10, "unit": "µS/cm" },
  "average_nitrate": { "value": 1.45, "unit": "mg/L" },
  "average_temperature": { "value": 22.30, "unit": "°C" }
}
```

### D. Run Prediction (`POST /predictions/predict`)

**Request Payload:**
```json
{
  "ph": 7.4,
  "dissolved_oxygen": 6.8,
  "bod": 2.1,
  "turbidity": 4.5,
  "tds": 240.0,
  "electrical_conductivity": 350.0,
  "nitrate": 1.2,
  "temperature": 21.5
}
```

**Response (Mock Mode `ML_MOCK_MODE=true`):**
```json
{
  "status": "MOCK",
  "prediction": "POTABLE",
  "confidence": 0.91,
  "probabilities": {
    "POTABLE": 0.91,
    "NON_POTABLE": 0.09
  },
  "model_version": "mock-water-quality-v1.0",
  "model_type": "MOCK_WATER_QUALITY_CLASSIFIER",
  "details": {
    "mock_note": "This is a synthetic mock response generated for offline API testing. Real ML integration is disabled or pending."
  }
}
```

**Response (Default Mode `ML_INTEGRATION_MODE=none`):**
```json
{
  "detail": "Machine learning prediction model is currently unavailable (not configured or deployed). Backend is awaiting model artifact (Option A) or ML microservice endpoint (Option B) from ML teammate."
}
```
*(HTTP Status: `503 Service Unavailable`)*

---

## 8. Machine Learning Integration & Teammate Handoff Specification

### A. Clear Division of Responsibilities
- **Backend Developer Responsibilities (Completed):**
  1. FastAPI route handling, Pydantic input validation, parameter boundary checks.
  2. Role-Based Access Control (`LAB_AUTHORITY`, `POLLUTION_OFFICIAL`, `ADMIN`).
  3. Reading stored database records for on-demand inference without mutating database records.
  4. Isolated service layer (`PredictionService`) with transparent exception mapping (`503`, `504`, `502`, `400`).
  5. Decoupled integration adapter supporting both local serialized artifacts and remote microservices.
  6. Strict scientific and architectural integrity: normal application mode defaults to `503 Service Unavailable` rather than inventing fake predictions.
- **ML Teammate Responsibilities (Independent Track):**
  1. Water quality dataset collection, cleaning, feature scaling, and preprocessing.
  2. Training, evaluation, hyperparameter tuning, metrics reporting (Accuracy, Precision, Recall, F1).
  3. Packaging and delivering the model via **Option A** (model file) or **Option B** (microservice).

### B. Deployment Options Supported by Backend

#### Option A: Local Model Artifact (In-Process)
- Set in `.env`:
  ```env
  ML_INTEGRATION_MODE=file
  ML_MODEL_PATH=models/water_quality_model.joblib
  ```
- **Handoff Artifact:** Deliver a trained scikit-learn / XGBoost model artifact (e.g. `joblib` or `pickle`) placed inside `backend/models/`.
- The object must implement `.predict(features)` and optionally `.predict_proba(features)`.

#### Option B: Remote ML Microservice (Decoupled HTTP Service)
- Set in `.env`:
  ```env
  ML_INTEGRATION_MODE=api
  ML_SERVICE_URL=http://localhost:8501/predict
  ML_SERVICE_TIMEOUT_SECONDS=5.0
  ```
- **Handoff Interface:** Run your model as a microservice (e.g. FastAPI, Flask, Streamlit, or Triton) accepting `POST {ML_SERVICE_URL}`.

### C. Expected ML Service Contract

#### Request Payload (Sent by Backend to ML Microservice)
```json
{
  "ph": 7.4,
  "dissolved_oxygen": 6.8,
  "bod": 2.1,
  "turbidity": 4.5,
  "tds": 240.0,
  "electrical_conductivity": 350.0,
  "nitrate": 1.2,
  "temperature": 21.5
}
```
*Note: `ph`, `dissolved_oxygen`, `bod`, `turbidity`, and `tds` are required numeric floats. `electrical_conductivity`, `nitrate`, and `temperature` are optional floats.*

#### Expected Response Format (Returned by ML Microservice)
```json
{
  "prediction": "POTABLE",
  "confidence": 0.942,
  "probabilities": {
    "POTABLE": 0.942,
    "NON_POTABLE": 0.058
  },
  "model_version": "rf-water-v2.1",
  "model_type": "RandomForestClassifier",
  "details": {
    "feature_importance": "pH and Turbidity had highest influence"
  }
}
```

### D. Backend HTTP Error Mapping
| Situation | HTTP Status Code | Response / Meaning |
| :--- | :--- | :--- |
| Missing or invalid measurement ranges (e.g. pH < 0 or > 14, negative DO) | `422 Unprocessable Entity` | Pydantic validation error detailing faulty fields |
| User missing Bearer JWT token | `401 Unauthorized` | Invalid or missing authentication |
| User is `CITIZEN` | `403 Forbidden` | Access forbidden: predictions restricted to authorized officials |
| Stored record not found (`GET /predictions/record/{id}`) | `404 Not Found` | Water quality measurement record does not exist |
| Stored record has missing required parameters | `400 Bad Request` | Record is incomplete for ML inference |
| ML model not configured (`ML_INTEGRATION_MODE=none`) | `503 Service Unavailable` | Model integration pending deployment |
| ML microservice exceeds timeout (`ML_SERVICE_TIMEOUT_SECONDS`) | `504 Gateway Timeout` | ML microservice took too long to respond |
| ML microservice returns invalid/malformed JSON or HTTP error | `502 Bad Gateway` | ML service integration failure |

---

## 9. Running Automated Tests

Run the full automated test suite using `pytest`:

```powershell
pytest -v
```

Or run individual day test suites:

```powershell
python test_auth_flow.py     # Day 2 Auth & RBAC (13 test scenarios)
python test_day3_flow.py     # Day 3 Water Quality CRUD (16 test scenarios)
pytest -v test_day4_flow.py  # Day 4 ML Predictions (10 test scenarios)
pytest -v test_day5_flow.py  # Day 5 GIS & Dashboards (11 test scenarios)
```
