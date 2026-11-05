"""
AquaWatch AI - Comprehensive Test Suite: Laboratory Authority Login & Immediate Activation Flow

Verifies:
1. Registration with valid active license (DEMO-LAB-2024-001) persists to DB with is_active=True and LAB_AUTHORITY role.
2. No administrator approval requirement: newly registered account is immediately active.
3. User can immediately log in using registered email and password (HTTP 200 OK + JWT Bearer token).
4. Login attempt with wrong password is rejected with HTTP 401 Unauthorized.
5. Existing accounts with valid licenses auto-activate safely on successful credential verification.
6. Case-insensitive email login works (e.g. mixed-case email).
7. Profile retrieval via /auth/me returns LAB_AUTHORITY role, active status, and laboratory information.
8. Protected endpoints (/auth/test/lab) accept the Bearer token.
9. Invalid or unregistered laboratory license is rejected with HTTP 400.
10. Inactive or revoked laboratory license is rejected with HTTP 400.
11. Non-lab / normal user accounts are forbidden from logging into the Laboratory Authority portal.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.main import app
from app.database import SessionLocal
from app.models import User, UserRole, LaboratoryLicense
from app.security import hash_password


class TestLabLoginFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.test_email = "immediate_lab_user@aquawatch.ai"
        cls.test_password = "ImmediateLabPass2024!"
        cls.test_name = "Dr. Immediate Access"
        cls.active_license = "DEMO-LAB-2024-001"

        cls.cleanup_emails = [
            cls.test_email,
            "existing_pending_test@aquawatch.ai",
            "normal_citizen_login_test@aquawatch.ai",
        ]
        cls.db.query(User).filter(User.email.in_(cls.cleanup_emails)).delete(synchronize_session=False)
        cls.db.commit()

        # Seed a normal citizen user to verify role-based login restriction
        normal_user = User(
            name="Normal Citizen Tester",
            email="normal_citizen_login_test@aquawatch.ai",
            hashed_password=hash_password("CitizenPass123!"),
            role=UserRole.NORMAL_USER,
            is_active=True,
        )
        cls.db.add(normal_user)

        # Seed a legacy pending user with a valid active license to test auto-activation on login
        pending_user = User(
            name="Legacy Pending Analyst",
            email="existing_pending_test@aquawatch.ai",
            hashed_password=hash_password("LegacyPass123!"),
            role=UserRole.LAB_AUTHORITY,
            is_active=False,
            laboratory_license_number="DEMO-LAB-2024-001",
            laboratory_name="AquaWatch Central Water Quality Laboratory",
        )
        cls.db.add(pending_user)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.db.query(User).filter(User.email.in_(cls.cleanup_emails)).delete(synchronize_session=False)
            cls.db.commit()
        finally:
            cls.db.close()

    def test_01_signup_with_active_license_immediately_active(self):
        """1. Register a new account with a valid active license number -> status is automatically active."""
        payload = {
            "name": self.test_name,
            "email": self.test_email,
            "password": self.test_password,
            "license_number": self.active_license,
            "designation": "Senior Water Quality Specialist",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["email"], self.test_email)
        self.assertEqual(data["role"], "LAB_AUTHORITY")
        self.assertEqual(data["laboratory_license_number"], self.active_license)
        self.assertTrue(data["is_active"], "Newly registered Lab Authority must be immediately active (no admin approval).")

        # Verify in database
        self.db.expire_all()
        db_user = self.db.query(User).filter(User.email == self.test_email).first()
        self.assertIsNotNone(db_user)
        self.assertTrue(db_user.is_active)
        print(f"[OK] Registration succeeded: ID #{data['id']}, role={data['role']}, is_active={data['is_active']} (Auto-activated in DB)")

    def test_02_login_immediately_without_approval(self):
        """2. User can immediately log in using their registered email and password."""
        res = self.client.post(
            "/auth/login",
            data={"username": self.test_email, "password": self.test_password},
        )
        self.assertEqual(res.status_code, 200, f"Expected 200 OK immediately after signup, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(data["expires_in"], 0)
        self.__class__.lab_token = data["access_token"]
        print("[OK] Immediate login succeeded without approval! JWT token received.")

    def test_03_login_with_wrong_password_rejected(self):
        """3. Incorrect password must still be rejected with HTTP 401 Unauthorized."""
        res = self.client.post(
            "/auth/login",
            data={"username": self.test_email, "password": "WrongPassword123!"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("incorrect", res.json()["detail"].lower())
        print("[OK] Incorrect password rejected with HTTP 401 Unauthorized")

    def test_04_existing_pending_account_auto_activates_on_login(self):
        """4. Existing account with active license auto-activates safely on login."""
        res = self.client.post(
            "/auth/login",
            data={"username": "existing_pending_test@aquawatch.ai", "password": "LegacyPass123!"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

        # Verify database is now updated to active
        self.db.expire_all()
        u = self.db.query(User).filter(User.email == "existing_pending_test@aquawatch.ai").first()
        self.assertTrue(u.is_active)
        print("[OK] Existing pending user auto-activated on login: is_active=True")

    def test_05_case_insensitive_login(self):
        """5. Login with case-variant email succeeds."""
        mixed_email = "IMMEDIATE_LAB_USER@AQUAWATCH.AI"
        res = self.client.post(
            "/auth/login",
            data={"username": mixed_email, "password": self.test_password},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())
        print("[OK] Case-insensitive email login verified.")

    def test_06_profile_fetch_auth_me(self):
        """6. Authenticated profile endpoint /auth/me returns LAB_AUTHORITY details and license."""
        token = getattr(self.__class__, "lab_token", None)
        self.assertIsNotNone(token, "Login token not available")

        res = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        profile = res.json()
        self.assertEqual(profile["email"], self.test_email)
        self.assertEqual(profile["role"], "LAB_AUTHORITY")
        self.assertEqual(profile["laboratory_license_number"], self.active_license)
        self.assertTrue(profile["is_active"])
        self.assertIsNotNone(profile["laboratory_name"])
        print(f"[OK] /auth/me verified: {profile['email']} ({profile['role']}), Active: {profile['is_active']}, Lab: {profile['laboratory_name']}")

    def test_07_protected_endpoint_access(self):
        """7. Protected test endpoint /auth/test/lab grants access with LAB_AUTHORITY token."""
        token = getattr(self.__class__, "lab_token", None)
        res = self.client.get("/auth/test/lab", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("verified LAB_AUTHORITY privileges", res.json()["message"])
        print("[OK] Protected endpoint /auth/test/lab accessible with Bearer token.")

    def test_08_invalid_license_still_rejected(self):
        """8. Invalid license number is rejected with HTTP 400 Bad Request."""
        payload = {
            "name": "Invalid License Applicant",
            "email": "invalid_license_test@aquawatch.ai",
            "password": "Password123!",
            "license_number": "INVALID-NOT-EXIST-000",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("not registered", res.json()["detail"].lower())
        print("[OK] Invalid license rejected during registration (HTTP 400)")

    def test_09_inactive_license_still_rejected(self):
        """9. Inactive or revoked license number is rejected with HTTP 400 Bad Request."""
        payload = {
            "name": "Inactive License Applicant",
            "email": "inactive_license_test@aquawatch.ai",
            "password": "Password123!",
            "license_number": "DEMO-LAB-INACTIVE-999",
        }
        res = self.client.post("/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("inactive", res.json()["detail"].lower())
        print("[OK] Inactive license rejected during registration (HTTP 400)")

    def test_10_normal_user_login_blocked(self):
        """10. Non-lab user (NORMAL_USER) cannot authenticate through Lab Authority login."""
        res = self.client.post(
            "/auth/login",
            data={"username": "normal_citizen_login_test@aquawatch.ai", "password": "CitizenPass123!"},
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("reserved exclusively for authorized laboratory authorities", res.json()["detail"].lower())
        print("[OK] Normal citizen login properly blocked from Lab Authority portal (HTTP 403 Forbidden).")


if __name__ == "__main__":
    unittest.main()
