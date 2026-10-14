"""
AquaWatch AI - Day 4 ML Prediction API Integration Test Suite

Test Coverage:
1. Input schema validation (pH 0-14, nonnegative DO/BOD/Turbidity/TDS)
2. Invalid & missing measurement inputs rejected with HTTP 422
3. Authentication & RBAC enforcement (401 on missing token, 403 for Citizen, allowed for Lab/Official/Admin)
4. Default/Normal mode: Model unavailable returns HTTP 503 Service Unavailable
5. External ML microservice timeout returns HTTP 504 Gateway Timeout
6. External ML microservice invalid response returns HTTP 502 Bad Gateway
7. Successful prediction in test mock mode returns HTTP 200 with status='MOCK'
8. /predictions/record/{id} returns 404 for nonexistent record
9. /predictions/record/{id} rejects incomplete measurement record with HTTP 400
10. /predictions/record/{id} succeeds on complete record without mutating database
11. Regression verification: Day 1, Day 2, Day 3, and Day 5 endpoints remain fully operational
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password, create_access_token
from app.services.prediction_service import (
    MLServiceIntegrationException,
    MLServiceTimeoutException,
    prediction_service,
)

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_day4_data():
    """
    Sets up controlled test fixtures for prediction tests.
    """
    db: Session = SessionLocal()

    test_emails = [
        "day4_citizen@aquawatch.org",
        "day4_lab@aquawatch.org",
        "day4_official@aquawatch.org",
        "day4_admin@aquawatch.org",
    ]

    # Clean old test data
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("DAY4_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("DAY4_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()

    # 1. Create users
    users = {
        "citizen": User(
            name="Day 4 Citizen",
            email="day4_citizen@aquawatch.org",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.NORMAL_USER,
            is_active=True,
        ),
        "lab": User(
            name="Day 4 Lab",
            email="day4_lab@aquawatch.org",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.LAB_AUTHORITY,
            is_active=True,
        ),
        "official": User(
            name="Day 4 Official",
            email="day4_official@aquawatch.org",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.LAB_AUTHORITY,
            is_active=True,
        ),
        "admin": User(
            name="Day 4 Admin",
            email="day4_admin@aquawatch.org",
            hashed_password=hash_password("Pass123!"),
            role=UserRole.LAB_AUTHORITY,
            is_active=True,
        ),
    }
    db.add_all(list(users.values()))
    db.commit()

    tokens = {
        role: create_access_token(data={"sub": u.email, "role": u.role.value})[0]
        for role, u in users.items()
    }
    headers = {role: {"Authorization": f"Bearer {t}"} for role, t in tokens.items()}

    # 2. Create test water body
    wb = WaterBody(
        name="DAY4_Test_River",
        water_body_type="river",
        location_name="Day 4 Test Station",
        latitude=28.6139,
        longitude=77.2090,
    )
    db.add(wb)
    db.commit()
    db.refresh(wb)

    # 3. Create a complete measurement record
    now = datetime.now(timezone.utc)
    rec_complete = WaterQualityRecord(
        water_body_id=wb.id,
        ph=7.5,
        dissolved_oxygen=6.5,
        bod=2.0,
        turbidity=4.0,
        tds=220.0,
        electrical_conductivity=340.0,
        nitrate=1.2,
        temperature=22.0,
        measured_at=now,
    )
    # 4. Create an incomplete measurement record (missing dissolved_oxygen and tds)
    rec_incomplete = WaterQualityRecord(
        water_body_id=wb.id,
        ph=7.2,
        dissolved_oxygen=None,  # Missing
        bod=2.5,
        turbidity=5.0,
        tds=None,               # Missing
        measured_at=now,
    )
    db.add_all([rec_complete, rec_incomplete])
    db.commit()
    db.refresh(rec_complete)
    db.refresh(rec_incomplete)

    yield {
        "headers": headers,
        "wb": wb,
        "rec_complete": rec_complete,
        "rec_incomplete": rec_incomplete,
    }

    # Teardown
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("DAY4_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("DAY4_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def test_prediction_input_validation(setup_day4_data):
    """Scenario 1 & 2: Input schema validation rejects out-of-bounds or missing parameters."""
    headers = setup_day4_data["headers"]["lab"]

    # Invalid pH (< 0) -> 422
    res_low_ph = client.post(
        "/predictions/predict",
        json={"ph": -1.0, "dissolved_oxygen": 6.0, "bod": 2.0, "turbidity": 4.0, "tds": 200.0},
        headers=headers,
    )
    assert res_low_ph.status_code == 422

    # Invalid pH (> 14) -> 422
    res_high_ph = client.post(
        "/predictions/predict",
        json={"ph": 15.0, "dissolved_oxygen": 6.0, "bod": 2.0, "turbidity": 4.0, "tds": 200.0},
        headers=headers,
    )
    assert res_high_ph.status_code == 422

    # Negative dissolved oxygen -> 422
    res_neg_do = client.post(
        "/predictions/predict",
        json={"ph": 7.0, "dissolved_oxygen": -2.0, "bod": 2.0, "turbidity": 4.0, "tds": 200.0},
        headers=headers,
    )
    assert res_neg_do.status_code == 422

    # Missing required field (e.g. missing turbidity) -> 422
    res_missing = client.post(
        "/predictions/predict",
        json={"ph": 7.0, "dissolved_oxygen": 6.0, "bod": 2.0, "tds": 200.0},
        headers=headers,
    )
    assert res_missing.status_code == 422


def test_prediction_authorization(setup_day4_data):
    """Scenario 3: Authentication and role-based authorization check."""
    valid_payload = {
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
    }

    # Unauthenticated request -> 401 Unauthorized
    res_unauth = client.post("/predictions/predict", json=valid_payload)
    assert res_unauth.status_code == 401

    # Authenticated as CITIZEN -> 403 Forbidden
    res_cit = client.post(
        "/predictions/predict",
        json=valid_payload,
        headers=setup_day4_data["headers"]["citizen"],
    )
    assert res_cit.status_code == 403


def test_model_unavailable_default_mode(setup_day4_data, monkeypatch):
    """Scenario 4: When ML integration is not deployed (mode='none'), returns HTTP 503."""
    # Ensure mock mode is disabled and integration is 'none'
    monkeypatch.setenv("ML_MOCK_MODE", "false")
    monkeypatch.setenv("ML_INTEGRATION_MODE", "none")
    prediction_service._refresh_config()

    valid_payload = {
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
    }

    res = client.post(
        "/predictions/predict",
        json=valid_payload,
        headers=setup_day4_data["headers"]["lab"],
    )
    assert res.status_code == 503
    assert "unavailable" in res.json()["detail"].lower()


def test_ml_service_timeout_handling(setup_day4_data, monkeypatch):
    """Scenario 5: External ML microservice timeout raises HTTP 504."""
    async def mock_timeout(*args, **kwargs):
        raise MLServiceTimeoutException("External ML microservice timed out.")

    monkeypatch.setattr(prediction_service, "predict", mock_timeout)

    valid_payload = {
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
    }

    res = client.post(
        "/predictions/predict",
        json=valid_payload,
        headers=setup_day4_data["headers"]["lab"],
    )
    assert res.status_code == 504
    assert "timed out" in res.json()["detail"].lower()


def test_ml_service_invalid_response_handling(setup_day4_data, monkeypatch):
    """Scenario 6: External ML microservice error or bad payload raises HTTP 502."""
    async def mock_bad_response(*args, **kwargs):
        raise MLServiceIntegrationException("Invalid response payload from external ML API.")

    monkeypatch.setattr(prediction_service, "predict", mock_bad_response)

    valid_payload = {
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
    }

    res = client.post(
        "/predictions/predict",
        json=valid_payload,
        headers=setup_day4_data["headers"]["lab"],
    )
    assert res.status_code == 502
    assert "invalid response" in res.json()["detail"].lower()


def test_successful_mock_prediction(setup_day4_data, monkeypatch):
    """Scenario 7: Explicit test mock mode returns HTTP 200 with clearly marked status='MOCK'."""
    monkeypatch.setenv("ML_MOCK_MODE", "true")
    prediction_service._refresh_config()

    valid_payload = {
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
    }

    res = client.post(
        "/predictions/predict",
        json=valid_payload,
        headers=setup_day4_data["headers"]["lab"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "MOCK"
    assert data["prediction"] in ("POTABLE", "NON_POTABLE")
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["model_version"] == "mock-test-v1.0"
    assert data["features_used"]["ph"] == 7.4


def test_predict_from_stored_record_nonexistent(setup_day4_data):
    """Scenario 8: GET /predictions/record/{id} returns 404 for nonexistent record."""
    res = client.get(
        "/predictions/record/999999",
        headers=setup_day4_data["headers"]["official"],
    )
    assert res.status_code == 404


def test_predict_from_stored_record_incomplete(setup_day4_data):
    """Scenario 9: GET /predictions/record/{id} returns 400 when record has missing core features."""
    rec_incomplete_id = setup_day4_data["rec_incomplete"].id
    res = client.get(
        f"/predictions/record/{rec_incomplete_id}",
        headers=setup_day4_data["headers"]["official"],
    )
    assert res.status_code == 400
    assert "missing required model parameters" in res.json()["detail"].lower()


def test_predict_from_stored_record_success_no_mutation(setup_day4_data, monkeypatch):
    """Scenario 10: Complete record succeeds in mock mode without mutating database."""
    monkeypatch.setenv("ML_MOCK_MODE", "true")
    prediction_service._refresh_config()

    rec_id = setup_day4_data["rec_complete"].id
    res = client.get(
        f"/predictions/record/{rec_id}",
        headers=setup_day4_data["headers"]["admin"],
    )
    assert res.status_code == 200
    assert res.json()["status"] == "MOCK"
    assert res.json()["features_used"]["ph"] == 7.5

    # Verify original database record is not mutated
    db: Session = SessionLocal()
    rec_db = db.query(WaterQualityRecord).filter(WaterQualityRecord.id == rec_id).first()
    assert rec_db is not None
    assert rec_db.ph == 7.5
    assert rec_db.dissolved_oxygen == 6.5
    db.close()


def test_regression_all_previous_days(setup_day4_data):
    """Scenario 11: Verify Day 1, Day 2, Day 3, and Day 5 endpoints continue operating."""
    headers_citizen = setup_day4_data["headers"]["citizen"]

    # Day 1
    assert client.get("/health").status_code == 200
    assert client.get("/health/db").status_code == 200

    # Day 2
    assert client.get("/auth/me", headers=headers_citizen).status_code == 200

    # Day 3
    assert client.get("/water-bodies", headers=headers_citizen).status_code == 200
    assert client.get("/water-quality", headers=headers_citizen).status_code == 200

    # Day 5
    assert client.get("/gis/locations").status_code == 200
    assert client.get("/dashboard/summary").status_code == 200
    assert client.get("/dashboard/water-quality-overview").status_code == 200


if __name__ == "__main__":
    pytest.main(["-v", "test_day4_flow.py"])
