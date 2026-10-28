"""
AquaWatch AI — Automated Test Suite for Water Safety Classification & Dummy Testing

Verifies:
1. Retrieval of predefined dummy test samples (Sample A, Sample B, Sample C).
2. Role-based access control on /water-quality/test (401 unauthenticated, 403 NORMAL_USER, 200 LAB_AUTHORITY).
3. Sample A evaluated by FastAPI backend returns SAFE (all 5 core parameters pass).
4. Sample B evaluated by FastAPI backend returns HARMFUL (all 5 parameters fail with detailed reasons).
5. Sample C evaluated by FastAPI backend returns SAFE (with boundary warnings for BOD and Turbidity).
6. Incomplete data (missing core parameters) evaluated by FastAPI backend returns INCONCLUSIVE.
7. Physically invalid parameters (pH outside 0-14, negative values) evaluated as INCONCLUSIVE.
8. Unestablished/disabled standard evaluated as INCONCLUSIVE.
9. Testing without persistence (verifying PostgreSQL record count remains unchanged).
10. Explicit persistence when save_to_db=True is requested.
11. Rejection when save_to_db=True without water_body_id (HTTP 400).
"""

import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import create_access_token, hash_password
from app.services.water_quality_classifier import evaluate_sample_safety


class TestWaterSafetyClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()

        cls.normal_email = "test_safety_normal@aquawatch.ai"
        cls.lab_email = "test_safety_lab@aquawatch.ai"

        normal_user = cls.db.query(User).filter(User.email == cls.normal_email).first()
        if not normal_user:
            normal_user = User(
                name="Test Normal Safety",
                email=cls.normal_email,
                hashed_password=hash_password("password123"),
                role=UserRole.NORMAL_USER,
                is_active=True,
            )
            cls.db.add(normal_user)

        lab_user = cls.db.query(User).filter(User.email == cls.lab_email).first()
        if not lab_user:
            lab_user = User(
                name="Test Lab Safety",
                email=cls.lab_email,
                hashed_password=hash_password("password123"),
                role=UserRole.LAB_AUTHORITY,
                is_active=True,
            )
            cls.db.add(lab_user)

        water_body = cls.db.query(WaterBody).first()
        if not water_body:
            water_body = WaterBody(
                name="Safety Test Water Body",
                water_body_type="river",
                location_name="Screening Basin",
                latitude=22.0,
                longitude=78.0,
            )
            cls.db.add(water_body)

        cls.db.commit()
        cls.db.refresh(normal_user)
        cls.db.refresh(lab_user)
        cls.db.refresh(water_body)

        cls.normal_token = create_access_token({"sub": normal_user.email, "role": UserRole.NORMAL_USER.value})[0]
        cls.lab_token = create_access_token({"sub": lab_user.email, "role": UserRole.LAB_AUTHORITY.value})[0]
        cls.water_body_id = water_body.id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_get_predefined_dummy_samples(self):
        """Verify GET /water-quality/demo-samples returns Sample A, B, and C with exact specifications."""
        response = self.client.get("/water-quality/demo-samples")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)

        sample_a = next(s for s in data if s["id"] == "sample-a")
        self.assertEqual(sample_a["ph"], 7.2)
        self.assertEqual(sample_a["dissolved_oxygen"], 7.0)
        self.assertEqual(sample_a["bod"], 2.0)
        self.assertEqual(sample_a["turbidity"], 3.0)
        self.assertEqual(sample_a["tds"], 250.0)

        sample_b = next(s for s in data if s["id"] == "sample-b")
        self.assertEqual(sample_b["ph"], 5.2)
        self.assertEqual(sample_b["dissolved_oxygen"], 3.0)
        self.assertEqual(sample_b["bod"], 8.0)
        self.assertEqual(sample_b["turbidity"], 25.0)
        self.assertEqual(sample_b["tds"], 900.0)

        sample_c = next(s for s in data if s["id"] == "sample-c")
        self.assertEqual(sample_c["ph"], 8.0)
        self.assertEqual(sample_c["dissolved_oxygen"], 6.0)
        self.assertEqual(sample_c["bod"], 3.0)
        self.assertEqual(sample_c["turbidity"], 5.0)
        self.assertEqual(sample_c["tds"], 400.0)
        print("[PASS] Test 1: Predefined dummy samples match required measurements.")

    def test_02_rbac_unauthenticated_returns_401(self):
        """Unauthenticated requests to /water-quality/test must receive HTTP 401."""
        payload = {"sample_name": "Sample A", "ph": 7.2, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0}
        response = self.client.post("/water-quality/test", json=payload)
        self.assertEqual(response.status_code, 401)
        print("[PASS] Test 2: Unauthenticated POST /water-quality/test rejected with 401.")

    def test_03_rbac_normal_user_returns_403(self):
        """NORMAL_USER requests to /water-quality/test must receive HTTP 403 Forbidden."""
        payload = {"sample_name": "Sample A", "ph": 7.2, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0}
        headers = {"Authorization": f"Bearer {self.normal_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Insufficient permissions", response.json()["detail"])
        print("[PASS] Test 3: NORMAL_USER POST /water-quality/test blocked with 403.")

    def test_04_sample_a_classified_as_safe(self):
        """Sample A meets all CPCB Class C / IS 10500 criteria and is classified as SAFE."""
        initial_count = self.db.query(WaterQualityRecord).count()
        payload = {
            "sample_name": "Sample A",
            "is_demo": True,
            "ph": 7.2,
            "dissolved_oxygen": 7.0,
            "bod": 2.0,
            "turbidity": 3.0,
            "tds": 250.0,
            "save_to_db": False,
        }
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["classification"], "SAFE")
        self.assertEqual(data["result_type"], "DEMO_RULE_BASED")
        self.assertEqual(len(data["failed_parameters"]), 0)
        self.assertEqual(len(data["passed_parameters"]), 5)
        self.assertIn("CPCB Class C", data["standard_name"])
        self.assertIn("microbial", data["limitations"].lower())
        self.assertFalse(data["persisted_to_database"])

        # Check parameter assessments list
        params = {p["parameter"]: p for p in data["parameter_assessments"]}
        self.assertEqual(params["ph"]["status"], "PASS")
        self.assertEqual(params["dissolved_oxygen"]["status"], "PASS")
        self.assertEqual(params["bod"]["status"], "PASS")
        self.assertEqual(params["turbidity"]["status"], "PASS")
        self.assertEqual(params["tds"]["status"], "PASS")

        # Database record count must NOT change
        new_count = self.db.query(WaterQualityRecord).count()
        self.assertEqual(initial_count, new_count)
        print("[PASS] Test 4: Sample A correctly classified as SAFE (0 DB mutation).")

    def test_05_sample_b_classified_as_harmful(self):
        """Sample B fails 5 out of 5 criteria and is classified as HARMFUL with detailed reasons."""
        payload = {
            "sample_name": "Sample B",
            "is_demo": True,
            "ph": 5.2,
            "dissolved_oxygen": 3.0,
            "bod": 8.0,
            "turbidity": 25.0,
            "tds": 900.0,
            "save_to_db": False,
        }
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["classification"], "HARMFUL")
        self.assertEqual(data["result_type"], "DEMO_RULE_BASED")
        self.assertEqual(len(data["failed_parameters"]), 5)
        self.assertIn("ph", data["failed_parameters"])
        self.assertIn("dissolved_oxygen", data["failed_parameters"])
        self.assertIn("bod", data["failed_parameters"])
        self.assertIn("turbidity", data["failed_parameters"])
        self.assertIn("tds", data["failed_parameters"])

        # Verify failing messages in reasons
        reasons_text = " ".join(data["reasons"])
        self.assertIn("Acidic", reasons_text)
        self.assertIn("Depleted Oxygen", reasons_text)
        self.assertIn("BOD", reasons_text)
        self.assertIn("Turbidity", reasons_text)
        self.assertIn("TDS", reasons_text)

        # Check parameter assessments status
        params = {p["parameter"]: p for p in data["parameter_assessments"]}
        self.assertEqual(params["ph"]["status"], "FAIL")
        self.assertEqual(params["dissolved_oxygen"]["status"], "FAIL")
        self.assertEqual(params["bod"]["status"], "FAIL")
        self.assertEqual(params["turbidity"]["status"], "FAIL")
        self.assertEqual(params["tds"]["status"], "FAIL")
        print("[PASS] Test 5: Sample B correctly classified as HARMFUL (all 5 failed parameters detailed).")

    def test_06_sample_c_classified_as_safe_with_boundary_warnings(self):
        """Sample C passes all criteria (SAFE) and generates boundary warnings for BOD (3.0) & Turbidity (5.0)."""
        payload = {
            "sample_name": "Sample C",
            "is_demo": True,
            "ph": 8.0,
            "dissolved_oxygen": 6.0,
            "bod": 3.0,
            "turbidity": 5.0,
            "tds": 400.0,
            "save_to_db": False,
        }
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["classification"], "SAFE")
        self.assertEqual(len(data["failed_parameters"]), 0)
        self.assertTrue(len(data["warnings"]) >= 2)
        warnings_text = " ".join(data["warnings"])
        self.assertIn("BOD", warnings_text)
        self.assertIn("Turbidity", warnings_text)
        print("[PASS] Test 6: Sample C classified as SAFE with threshold boundary warnings.")

    def test_07_incomplete_measurements_classified_as_inconclusive(self):
        """When core parameters are missing or insufficient, classification must be INCONCLUSIVE."""
        payload = {
            "sample_name": "Incomplete Sample (pH only)",
            "is_demo": True,
            "ph": 7.4,
            "dissolved_oxygen": None,
            "bod": None,
            "turbidity": None,
            "tds": None,
            "save_to_db": False,
        }
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["classification"], "INCONCLUSIVE")
        self.assertIn("Missing required core measurement(s)", " ".join(data["reasons"]))

        params = {p["parameter"]: p for p in data["parameter_assessments"]}
        self.assertEqual(params["dissolved_oxygen"]["status"], "INSUFFICIENT")
        self.assertEqual(params["bod"]["status"], "INSUFFICIENT")
        print("[PASS] Test 7: Incomplete data classified as INCONCLUSIVE with missing parameters listed.")

    def test_08_physically_invalid_data_classified_as_inconclusive(self):
        """When measurements contain impossible numbers (e.g. pH=16 or DO=-5), classification is INCONCLUSIVE."""
        payload = {
            "sample_name": "Physically Invalid Sample",
            "is_demo": True,
            "ph": 16.5,  # pH cannot exceed 14
            "dissolved_oxygen": -4.0,  # DO cannot be negative
            "bod": 2.0,
            "turbidity": 3.0,
            "tds": 250.0,
            "save_to_db": False,
        }
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["classification"], "INCONCLUSIVE")
        reasons_text = " ".join(data["reasons"])
        self.assertIn("Physically invalid", reasons_text)
        print("[PASS] Test 8: Physically invalid measurements correctly classified as INCONCLUSIVE.")

    def test_09_disabled_or_unestablished_standard_returns_inconclusive(self):
        """If standard is not established/enabled, evaluate_sample_safety must return INCONCLUSIVE."""
        sample_data = {"ph": 7.2, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0}
        eval_result = evaluate_sample_safety(sample_data, sample_name="Disabled Test", force_enabled=False)
        self.assertEqual(eval_result["classification"], "INCONCLUSIVE")
        self.assertIn("not established or enabled", " ".join(eval_result["reasons"]))
        print("[PASS] Test 9: Disabled standard returns INCONCLUSIVE (never falsely claims water is safe).")

    def test_10_explicit_persistence_with_water_body(self):
        """When save_to_db=True with valid water_body_id, record is persisted and ID returned."""
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        payload = {
            "sample_name": "Sample A Explicit Persist",
            "is_demo": True,
            "ph": 7.2,
            "dissolved_oxygen": 7.0,
            "bod": 2.0,
            "turbidity": 3.0,
            "tds": 250.0,
            "save_to_db": True,
            "water_body_id": self.water_body_id,
        }
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["persisted_to_database"])
        self.assertIsNotNone(data["persisted_record_id"])

        record = self.db.query(WaterQualityRecord).filter(WaterQualityRecord.id == data["persisted_record_id"]).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.ph, 7.2)
        print(f"[PASS] Test 10: Explicit persistence succeeded (Record #{record.id}).")

    def test_11_explicit_persistence_missing_water_body_returns_400(self):
        """When save_to_db=True without water_body_id, backend returns HTTP 400 Bad Request."""
        headers = {"Authorization": f"Bearer {self.lab_token}"}
        payload = {
            "sample_name": "Missing Water Body",
            "ph": 7.2,
            "dissolved_oxygen": 7.0,
            "bod": 2.0,
            "turbidity": 3.0,
            "tds": 250.0,
            "save_to_db": True,
            "water_body_id": None,
        }
        response = self.client.post("/water-quality/test", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("water_body_id is required", response.json()["detail"])
        print("[PASS] Test 11: Explicit persistence without water_body_id rejected with 400.")


if __name__ == "__main__":
    unittest.main()
