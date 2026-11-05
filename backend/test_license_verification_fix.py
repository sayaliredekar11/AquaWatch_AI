"""
AquaWatch AI - Test Suite: Verify Laboratory License Verification Fix
Tests:
1. DEMO-LAB-2024-001 is accepted during signup.
2. DEMO-LAB-2024-002 is accepted during signup.
3. DEMO-LAB-2024-003 is accepted during signup.
4. DEMO-LAB-INACTIVE-999 is rejected during signup (400 Bad Request).
5. Unregistered license number is rejected during signup (400 Bad Request).
6. Empty license number is rejected during signup (400 Bad Request).
7. Duplicate email is rejected during signup (400 Bad Request).
8. Multiple staff members registering with DEMO-LAB-2024-001 both succeed and link to the same laboratory record.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.main import app
from app.database import SessionLocal
from app.models import User, LaboratoryLicense


class TestLicenseVerificationFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.test_emails = [
            "fix_tester_demo1@aquawatch.ai",
            "fix_tester_demo2@aquawatch.ai",
            "fix_tester_demo3@aquawatch.ai",
            "fix_tester_inactive@aquawatch.ai",
            "fix_tester_invalid@aquawatch.ai",
            "fix_staff_alpha@aquawatch.ai",
            "fix_staff_beta@aquawatch.ai",
        ]
        # Clean up any leftover test accounts
        cls.db.query(User).filter(User.email.in_(cls.test_emails)).delete(synchronize_session=False)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.query(User).filter(User.email.in_(cls.test_emails)).delete(synchronize_session=False)
            cls.db.commit()
        finally:
            cls.db.close()

    def test_01_preflight_active_licenses(self):
        """Verify pre-flight validation endpoint accepts all 3 active demo licenses."""
        demos = [
            ("DEMO-LAB-2024-001", "AquaWatch Central Water Quality Laboratory"),
            ("DEMO-LAB-2024-002", "Western Maharashtra Regional Testing Laboratory"),
            ("DEMO-LAB-2024-003", "Krishna Basin Water Quality Testing Facility"),
        ]
        for lic, expected_name in demos:
            res = self.client.get(f"/auth/licenses/validate?license_number={lic}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["valid"], f"Expected {lic} to be valid")
            self.assertTrue(data["is_active"], f"Expected {lic} to be active")
            self.assertEqual(data["laboratory_name"], expected_name)
            print(f"[OK] Pre-flight for {lic}: Verified -> {data['laboratory_name']}")

    def test_02_preflight_inactive_license(self):
        """Verify pre-flight validation rejects inactive demo license."""
        res = self.client.get("/auth/licenses/validate?license_number=DEMO-LAB-INACTIVE-999")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["valid"])
        self.assertFalse(data["is_active"])
        self.assertIn("inactive or suspended", data["message"].lower())
        print("[OK] Pre-flight rejected DEMO-LAB-INACTIVE-999 as expected")

    def test_03_preflight_invalid_license(self):
        """Verify pre-flight validation rejects unregistered license."""
        res = self.client.get("/auth/licenses/validate?license_number=FAKE-LICENSE-999")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["valid"])
        self.assertIn("not registered", data["message"].lower())
        print("[OK] Pre-flight rejected FAKE-LICENSE-999 as expected")

    def test_04_signup_demo_lab_001_succeeds(self):
        """Verify signup with DEMO-LAB-2024-001 is accepted."""
        email = "fix_tester_demo1@aquawatch.ai"
        payload = {
            "name": "Dr. Central Analyst",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-001",
            "designation": "Chief Chemist",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed: {res.text}")
        data = res.json()
        self.assertEqual(data["email"], email)
        self.assertEqual(data["laboratory_license_number"], "DEMO-LAB-2024-001")
        self.assertEqual(data["laboratory_name"], "AquaWatch Central Water Quality Laboratory")
        self.assertIsNotNone(data["laboratory_id"])
        print("[OK] Signup with DEMO-LAB-2024-001 succeeded")

    def test_05_signup_demo_lab_002_succeeds(self):
        """Verify signup with DEMO-LAB-2024-002 is accepted."""
        email = "fix_tester_demo2@aquawatch.ai"
        payload = {
            "name": "Dr. Regional Analyst",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-002",
            "designation": "Water Quality Specialist",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed: {res.text}")
        data = res.json()
        self.assertEqual(data["email"], email)
        self.assertEqual(data["laboratory_license_number"], "DEMO-LAB-2024-002")
        self.assertEqual(data["laboratory_name"], "Western Maharashtra Regional Testing Laboratory")
        print("[OK] Signup with DEMO-LAB-2024-002 succeeded")

    def test_06_signup_demo_lab_003_succeeds(self):
        """Verify signup with DEMO-LAB-2024-003 is accepted."""
        email = "fix_tester_demo3@aquawatch.ai"
        payload = {
            "name": "Dr. Basin Analyst",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-003",
            "designation": "Environmental Officer",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed: {res.text}")
        data = res.json()
        self.assertEqual(data["email"], email)
        self.assertEqual(data["laboratory_license_number"], "DEMO-LAB-2024-003")
        self.assertEqual(data["laboratory_name"], "Krishna Basin Water Quality Testing Facility")
        print("[OK] Signup with DEMO-LAB-2024-003 succeeded")

    def test_07_signup_inactive_license_rejected(self):
        """Verify signup with DEMO-LAB-INACTIVE-999 is rejected."""
        payload = {
            "name": "Inactive Lab Tester",
            "email": "fix_tester_inactive@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-INACTIVE-999",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("inactive, suspended, or revoked", res.json()["detail"].lower())
        print("[OK] Signup with DEMO-LAB-INACTIVE-999 rejected with HTTP 400")

    def test_08_signup_invalid_license_rejected(self):
        """Verify signup with unregistered license is rejected."""
        payload = {
            "name": "Invalid Lab Tester",
            "email": "fix_tester_invalid@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "UNREGISTERED-99999",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("not registered", res.json()["detail"].lower())
        print("[OK] Signup with UNREGISTERED-99999 rejected with HTTP 400")

    def test_09_signup_empty_license_rejected(self):
        """Verify signup with empty license is rejected."""
        payload = {
            "name": "Empty Lab Tester",
            "email": "fix_tester_invalid@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "   ",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("license number is required", res.json()["detail"].lower())
        print("[OK] Signup with empty license rejected with HTTP 400")

    def test_10_signup_duplicate_email_rejected(self):
        """Verify signup with already registered email is rejected."""
        payload = {
            "name": "Duplicate Tester",
            "email": "fix_tester_demo1@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-001",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already registered", res.json()["detail"].lower())
        print("[OK] Duplicate email rejected with HTTP 400")

    def test_11_multiple_staff_accounts_same_license(self):
        """Verify multiple staff accounts can register under DEMO-LAB-2024-001 and associate with same lab record."""
        payload_a = {
            "name": "Staff Chemist Alpha",
            "email": "fix_staff_alpha@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-001",
            "designation": "Chemist A",
        }
        payload_b = {
            "name": "Staff Microbiologist Beta",
            "email": "fix_staff_beta@aquawatch.ai",
            "password": "SecurePassword123!",
            "license_number": "DEMO-LAB-2024-001",
            "designation": "Microbiologist B",
        }

        r_a = self.client.post("/auth/register", json=payload_a)
        self.assertEqual(r_a.status_code, 201)
        r_b = self.client.post("/auth/register", json=payload_b)
        self.assertEqual(r_b.status_code, 201)

        user_a = self.db.query(User).filter(User.email == "fix_staff_alpha@aquawatch.ai").first()
        user_b = self.db.query(User).filter(User.email == "fix_staff_beta@aquawatch.ai").first()

        self.assertIsNotNone(user_a)
        self.assertIsNotNone(user_b)
        self.assertEqual(user_a.laboratory_id, user_b.laboratory_id)
        self.assertEqual(user_a.laboratory_license_number, "DEMO-LAB-2024-001")
        self.assertEqual(user_b.laboratory_license_number, "DEMO-LAB-2024-001")
        print("[OK] Multiple staff accounts on DEMO-LAB-2024-001 verified successfully")


if __name__ == "__main__":
    unittest.main()
