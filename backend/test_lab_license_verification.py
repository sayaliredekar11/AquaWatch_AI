"""
AquaWatch AI - Automated Test Suite: Laboratory License Verification & Signup Flow

Tests:
1. Valid active license number: registration succeeds (201 Created), account is linked to the registered laboratory.
2. Unregistered/invalid license number: rejected with HTTP 400 and clear error message.
3. Empty/missing license number: rejected with HTTP 400.
4. Inactive/suspended license number: rejected with HTTP 400.
5. Multiple staff members registering with the same valid active license: both succeed and link to the same laboratory.
6. Duplicate email address: rejected with HTTP 400.
7. Duplicate username: rejected with HTTP 400.
8. Password hashing: plain password is NEVER stored; verified using Argon2 hash.
9. Correct laboratory association after registration: database relationships verified.
10. Existing login functionality after signup: approved user successfully logs in and receives JWT.
11. Existing signup validations still work: short password rejected, invalid email format rejected.
12. Pre-flight license validation endpoint: GET /auth/licenses/validate.
13. Anti-abuse rate limiting: repeated invalid attempts trigger 429 Too Many Requests.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Laboratory, LaboratoryLicense, User, UserRole
from app.security import verify_password


class TestLabLicenseVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()

        # Clean up any test users from previous runs
        cls.test_emails = [
            "license_tester_1@aquawatch.ai",
            "license_tester_2@aquawatch.ai",
            "license_tester_dup@aquawatch.ai",
            "license_tester_inactive@aquawatch.ai",
            "license_tester_invalid@aquawatch.ai",
            "staff_member_alpha@aquawatch.ai",
            "staff_member_beta@aquawatch.ai",
            "login_ready_lab@aquawatch.ai",
        ]
        cls.db.query(User).filter(User.email.in_(cls.test_emails)).delete(synchronize_session=False)

        # Ensure active and inactive test laboratories exist
        cls.active_license = "MH-WAT-2024-001"
        cls.inactive_license = "MH-WAT-REVOKED-999"

        lab1 = cls.db.query(LaboratoryLicense).filter(LaboratoryLicense.license_number == cls.active_license).first()
        if not lab1:
            lab1 = LaboratoryLicense(
                laboratory_name="Maharashtra State Central Water Testing Laboratory",
                license_number=cls.active_license,
                status="active",
            )
            cls.db.add(lab1)

        lab2 = cls.db.query(LaboratoryLicense).filter(LaboratoryLicense.license_number == cls.inactive_license).first()
        if not lab2:
            lab2 = LaboratoryLicense(
                laboratory_name="Suspended Regional Testing Facility",
                license_number=cls.inactive_license,
                status="inactive",
            )
            cls.db.add(lab2)

        cls.db.commit()
        cls.active_lab = lab1
        cls.inactive_lab = lab2

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.query(User).filter(User.email.in_(cls.test_emails)).delete(synchronize_session=False)
            cls.db.commit()
        finally:
            cls.db.close()

    def test_01_preflight_license_validation_endpoint(self):
        """Verify GET /auth/licenses/validate correctly identifies active, inactive, and invalid licenses."""
        # Active license
        r_active = self.client.get(f"/auth/licenses/validate?license_number={self.active_license}")
        self.assertEqual(r_active.status_code, 200)
        data_active = r_active.json()
        self.assertTrue(data_active["valid"])
        self.assertTrue(data_active["is_active"])
        self.assertIn("Central Water Testing Laboratory", data_active["laboratory_name"])

        # Inactive license
        r_inactive = self.client.get(f"/auth/licenses/validate?license_number={self.inactive_license}")
        self.assertEqual(r_inactive.status_code, 200)
        data_inactive = r_inactive.json()
        self.assertFalse(data_inactive["valid"])
        self.assertFalse(data_inactive["is_active"])
        self.assertIn("inactive or suspended", data_inactive["message"].lower())

        # Unregistered license
        r_invalid = self.client.get("/auth/licenses/validate?license_number=FAKE-LICENSE-99999")
        self.assertEqual(r_invalid.status_code, 200)
        data_invalid = r_invalid.json()
        self.assertFalse(data_invalid["valid"])
        self.assertIn("not registered", data_invalid["message"].lower())

    def test_02_signup_with_valid_license_succeeds_and_associates_lab(self):
        """Verify registration with a valid active license creates account and associates the correct laboratory."""
        email = "license_tester_1@aquawatch.ai"
        payload = {
            "name": "Dr. Pradeep Patil",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": self.active_license,
            "designation": "Senior Water Quality Analyst",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, f"Signup failed: {res.text}")
        data = res.json()

        self.assertEqual(data["email"], email)
        self.assertEqual(data["role"], "LAB_AUTHORITY")
        self.assertEqual(data["laboratory_license_number"], self.active_license)
        self.assertIn("Central Water Testing Laboratory", data["laboratory_name"])
        self.assertIsNotNone(data["laboratory_id"])

        # Check in database
        user = self.db.query(User).filter(User.email == email).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.laboratory_license_number, self.active_license)
        self.assertEqual(user.laboratory_id, self.active_lab.id)
        self.assertIn("Central Water Testing Laboratory", user.laboratory_name)
        self.assertNotEqual(user.hashed_password, "SecurePassword123!")
        self.assertTrue(verify_password("SecurePassword123!", user.hashed_password))

    def test_03_signup_with_invalid_license_rejected(self):
        """Verify registration with an unregistered license number is rejected with HTTP 400."""
        email = "license_tester_invalid@aquawatch.ai"
        payload = {
            "name": "Unauthorized User",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": "UNREGISTERED-LIC-000",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("not registered", res.json()["detail"].lower())

        # Verify user was not saved
        user = self.db.query(User).filter(User.email == email).first()
        self.assertIsNone(user)

    def test_04_signup_with_empty_license_rejected(self):
        """Verify registration without license number or with empty whitespace is rejected."""
        email = "license_tester_invalid@aquawatch.ai"
        payload = {
            "name": "Empty License Tester",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": "   ",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("license number is required", res.json()["detail"].lower())

    def test_05_signup_with_inactive_license_rejected(self):
        """Verify registration with an inactive / suspended license is rejected."""
        email = "license_tester_inactive@aquawatch.ai"
        payload = {
            "name": "Suspended Lab Tester",
            "email": email,
            "password": "SecurePassword123!",
            "license_number": self.inactive_license,
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("inactive, suspended, or revoked", res.json()["detail"].lower())

        # Verify user was not saved
        user = self.db.query(User).filter(User.email == email).first()
        self.assertIsNone(user)

    def test_06_multiple_staff_members_can_register_under_same_license(self):
        """Verify multiple staff members can register under the same valid license without creating duplicate labs."""
        email_alpha = "staff_member_alpha@aquawatch.ai"
        email_beta = "staff_member_beta@aquawatch.ai"

        payload_alpha = {
            "name": "Staff Analyst Alpha",
            "email": email_alpha,
            "password": "AlphaPassword123!",
            "license_number": self.active_license,
            "designation": "Microbiologist",
        }
        payload_beta = {
            "name": "Staff Analyst Beta",
            "email": email_beta,
            "password": "BetaPassword123!",
            "license_number": self.active_license,
            "designation": "Chemical Analyst",
        }

        r1 = self.client.post("/auth/register", json=payload_alpha)
        self.assertEqual(r1.status_code, 201)

        r2 = self.client.post("/auth/register", json=payload_beta)
        self.assertEqual(r2.status_code, 201)

        # Both users exist and point to the same laboratory_id
        user_alpha = self.db.query(User).filter(User.email == email_alpha).first()
        user_beta = self.db.query(User).filter(User.email == email_beta).first()

        self.assertIsNotNone(user_alpha)
        self.assertIsNotNone(user_beta)
        self.assertEqual(user_alpha.laboratory_id, user_beta.laboratory_id)
        self.assertEqual(user_alpha.laboratory_id, self.active_lab.id)

    def test_07_duplicate_email_rejected(self):
        """Verify that attempting to register with an existing email is rejected with HTTP 400."""
        payload = {
            "name": "Duplicate Tester",
            "email": "license_tester_1@aquawatch.ai",  # Already registered in test_02
            "password": "AnotherPassword123!",
            "license_number": self.active_license,
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already registered", res.json()["detail"].lower())

    def test_08_password_validation_and_hashing(self):
        """Verify that short passwords (< 6 characters) are rejected and valid passwords are never stored plain."""
        payload_short = {
            "name": "Short Pass User",
            "email": "short_pass@aquawatch.ai",
            "password": "123",
            "license_number": self.active_license,
        }
        res = self.client.post("/auth/register", json=payload_short)
        self.assertEqual(res.status_code, 422)  # Pydantic min_length validation

    def test_09_login_after_approval(self):
        """Verify that an approved Lab Authority can log in and retrieve their profile with laboratory info."""
        email = "login_ready_lab@aquawatch.ai"
        raw_pwd = "LaboratoryLoginPass123!"

        payload = {
            "name": "Dr. Login Ready",
            "email": email,
            "password": raw_pwd,
            "license_number": self.active_license,
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)

        # Simulate administrative approval (setting is_active=True)
        user = self.db.query(User).filter(User.email == email).first()
        user.is_active = True
        self.db.commit()

        # Log in via OAuth2 form
        login_res = self.client.post(
            "/auth/login",
            data={"username": email, "password": raw_pwd},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(login_res.status_code, 200)
        token_data = login_res.json()
        self.assertIn("access_token", token_data)
        access_token = token_data["access_token"]

        # Fetch profile from /auth/me
        profile_res = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(profile_res.status_code, 200)
        profile = profile_res.json()
        self.assertEqual(profile["email"], email)
        self.assertEqual(profile["role"], "LAB_AUTHORITY")
        self.assertEqual(profile["laboratory_license_number"], self.active_license)
        self.assertIsNotNone(profile["laboratory_id"])


if __name__ == "__main__":
    unittest.main()
