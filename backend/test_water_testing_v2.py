"""
AquaWatch AI — Automated Test Suite for Water Testing Page V2

Verifies:
1. Submission of water testing sample with all 14 parameters, sample info, and lab info.
2. Location ID requirement: 400 when missing, 404 when non-existent.
3. Decision tree ML model execution returning numerical WQI and WQI category.
4. Database persistence of all 14 parameters and metadata in PostgreSQL.
5. Automatic A4 PDF report generation, validation of PDF binary structure (%PDF-1.4).
6. GET /water-quality/reports/{report_id}/download endpoint returning HTTP 200 and application/pdf.
7. GET /water-quality/reports listing historical reports and filtering by sample_id / report_id.
8. Preservation of history: successive tests on the same location create distinct records without overwriting.
"""

import os
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import create_access_token, hash_password


class TestWaterTestingV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()

        cls.lab_email = "lab_v2_tester@aquawatch.ai"
        cls.normal_email = "normal_v2_tester@aquawatch.ai"

        lab_user = cls.db.query(User).filter(User.email == cls.lab_email).first()
        if not lab_user:
            lab_user = User(
                name="Dr. Tester V2",
                email=cls.lab_email,
                hashed_password=hash_password("password123"),
                role=UserRole.LAB_AUTHORITY,
                is_active=True,
            )
            cls.db.add(lab_user)

        normal_user = cls.db.query(User).filter(User.email == cls.normal_email).first()
        if not normal_user:
            normal_user = User(
                name="Normal Citizen",
                email=cls.normal_email,
                hashed_password=hash_password("password123"),
                role=UserRole.NORMAL_USER,
                is_active=True,
            )
            cls.db.add(normal_user)

        water_body = cls.db.query(WaterBody).filter(WaterBody.name == "Krishna River - Test Point").first()
        if not water_body:
            water_body = WaterBody(
                name="Krishna River - Test Point",
                water_body_type="river",
                location_name="Sangli Ghat",
                latitude=16.8524,
                longitude=74.5815,
            )
            cls.db.add(water_body)

        cls.db.commit()
        cls.db.refresh(lab_user)
        cls.db.refresh(normal_user)
        cls.db.refresh(water_body)

        cls.lab_token = create_access_token({"sub": lab_user.email, "role": UserRole.LAB_AUTHORITY.value})[0]
        cls.normal_token = create_access_token({"sub": normal_user.email, "role": UserRole.NORMAL_USER.value})[0]
        cls.water_body_id = water_body.id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_missing_location_id_rejected(self):
        """Verify that submitting without water_body_id returns HTTP 400."""
        payload = {
            "ph": 7.4,
            "dissolved_oxygen": 6.8,
            "bod": 2.2,
            "turbidity": 4.1,
            "tds": 280.0,
        }
        res = self.client.post(
            "/water-quality/test",
            json=payload,
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("location is required", res.json().get("detail", "").lower())

    def test_02_invalid_location_id_returns_404(self):
        """Verify that submitting with non-existent water_body_id returns HTTP 404."""
        payload = {
            "water_body_id": 9999999,
            "ph": 7.4,
            "dissolved_oxygen": 6.8,
            "bod": 2.2,
            "turbidity": 4.1,
            "tds": 280.0,
        }
        res = self.client.post(
            "/water-quality/test",
            json=payload,
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(res.status_code, 404)

    def test_03_submit_all_14_parameters_and_generate_report(self):
        """Verify submission of all 14 parameters, ML execution, DB persistence, and PDF creation."""
        sample_id = f"SMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "water_body_id": self.water_body_id,
            "sample_id": sample_id,
            "sample_type": "surface_water",
            "laboratory_name": "Maharashtra State Water Testing Central Lab",
            "lab_authority_name": "Dr. Tester V2",
            "testing_date": datetime.now(timezone.utc).isoformat(),
            "testing_method": "Standard Methods (APHA 23rd Edition)",
            "remarks": "Automated test sample verification for 14 parameters.",
            # 14 Laboratory Parameters:
            "ph": 7.45,
            "dissolved_oxygen": 6.8,
            "bod": 2.1,
            "cod": 12.0,
            "turbidity": 3.8,
            "tds": 290.0,
            "conductivity": 450.0,
            "temperature": 24.5,
            "nitrate": 4.2,
            "phosphate": 0.35,
            "chloride": 32.0,
            "total_coliform": 45.0,
            "fecal_coliform": 10.0,
            "ammonia_n": 0.25,
            "sulphate": 28.0,
        }

        res = self.client.post(
            "/water-quality/test",
            json=payload,
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(res.status_code, 200, f"Submission failed: {res.text}")
        data = res.json()

        # Check response structure
        self.assertIn("sample_id", data)
        self.assertEqual(data["sample_id"], sample_id)
        self.assertIn("report_id", data)
        self.assertTrue(data["report_id"].startswith("REP-"))
        self.assertIn("report_download_url", data)
        self.assertIsNotNone(data["wqi_score"])
        self.assertIsNotNone(data["wqi_category"])
        self.assertIn("is_safe", data)
        self.assertIn("safety_status", data)

        report_id = data["report_id"]

        # Check database persistence
        record = self.db.query(WaterQualityRecord).filter(WaterQualityRecord.report_id == report_id).first()
        self.assertIsNotNone(record, "Record was not persisted in database!")
        self.assertEqual(record.sample_id, sample_id)
        self.assertEqual(record.water_body_id, self.water_body_id)
        self.assertAlmostEqual(record.ph, 7.45, places=2)
        self.assertAlmostEqual(record.phosphate, 0.35, places=2)
        self.assertAlmostEqual(record.sulphate, 28.0, places=2)
        self.assertAlmostEqual(record.ammonia_n, 0.25, places=2)
        self.assertEqual(record.laboratory_name, "Maharashtra State Water Testing Central Lab")
        self.assertEqual(record.lab_authority_name, "Dr. Tester V2")
        self.assertIsNotNone(record.pdf_path)

        # Verify PDF file on disk
        self.assertTrue(os.path.exists(record.pdf_path), f"PDF file does not exist at {record.pdf_path}")
        file_size = os.path.getsize(record.pdf_path)
        self.assertGreater(file_size, 5000, f"PDF file is unexpectedly small: {file_size} bytes")

        with open(record.pdf_path, "rb") as f:
            pdf_bytes = f.read(10)
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"), "File is not a valid PDF")
            f.seek(0)
            full_pdf_text = f.read().decode("latin-1")
            self.assertIn("WATER QUALITY ANALYSIS REPORT", full_pdf_text)
            self.assertNotIn("AquaWatch", full_pdf_text, "AquaWatch branding must NOT appear in formal lab PDF report")
            self.assertIn("[ Signature of Authorized Signatory ]", full_pdf_text)
            self.assertIn("AUTHENTICITY NOTICE", full_pdf_text)
            self.assertIn("Page 1 of", full_pdf_text)

        # Test download endpoint
        dl_res = self.client.get(f"/water-quality/reports/{report_id}/download")
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res.headers.get("content-type"), "application/pdf")
        self.assertGreater(len(dl_res.content), 5000)

        # Test historical reports listing endpoint
        list_res = self.client.get(
            "/water-quality/reports?limit=10",
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.json()
        self.assertIn("items", list_data)
        self.assertGreater(list_data["total"], 0)

        # Test searching reports by Sample ID
        search_res = self.client.get(
            f"/water-quality/reports?search={sample_id}",
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(search_res.status_code, 200)
        search_data = search_res.json()
        self.assertEqual(search_data["total"], 1)
        self.assertEqual(search_data["items"][0]["sample_id"], sample_id)

        # Test searching reports by Report ID
        search_rep = self.client.get(
            f"/water-quality/reports?search={report_id}",
            headers={"Authorization": f"Bearer {self.lab_token}"},
        )
        self.assertEqual(search_rep.status_code, 200)
        rep_data = search_rep.json()
        self.assertEqual(rep_data["total"], 1)
        self.assertEqual(rep_data["items"][0]["report_id"], report_id)

    def test_04_successive_tests_preserve_history(self):
        """Verify that testing the same location multiple times preserves history and does not overwrite."""
        count_before = self.db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body_id == self.water_body_id
        ).count()

        for i in range(2):
            payload = {
                "water_body_id": self.water_body_id,
                "ph": 7.1 + (i * 0.2),
                "dissolved_oxygen": 6.5,
                "bod": 2.0,
                "turbidity": 3.0,
                "tds": 250.0,
            }
            res = self.client.post(
                "/water-quality/test",
                json=payload,
                headers={"Authorization": f"Bearer {self.lab_token}"},
            )
            self.assertEqual(res.status_code, 200)

        count_after = self.db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body_id == self.water_body_id
        ).count()
        self.assertEqual(count_after, count_before + 2)


if __name__ == "__main__":
    unittest.main()
