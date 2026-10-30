"""
AquaWatch AI - Comprehensive Lab Authority Signup Flow & RBAC Test Suite

Verifies:
1. Signup API without invitation token (HTTP 201 Created)
2. Safe account creation: role strictly assigned as LAB_AUTHORITY (client tampering blocked)
3. Duplicate-email handling (HTTP 400 Bad Request)
4. Password hashing verification (Argon2 hashed, plain password not stored)
5. Restricted policy: Newly registered user is pending approval (is_active=False)
6. Login before approval rejected (HTTP 403 Forbidden)
7. Administrator approval workflow (assign_lab_authority.py --approve)
8. Login after approval succeeds with valid Bearer token (HTTP 200 OK)
9. Authenticated profile (/auth/me) matches LAB_AUTHORITY
10. Protected endpoints require valid LAB_AUTHORITY token (401 / 403)
11. Public monitoring endpoints open without login (HTTP 200 OK)
12. Pre-authorized email signup creates immediately active account
"""

import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal, engine
from app.models import User, UserRole, LabInvitation
from app.security import hash_password, create_access_token

client = TestClient(app)


def run_tests():
    print("=" * 80)
    print("AQUAWATCH AI - LAB AUTHORITY SIGNUP & AUTHORIZATION TEST SUITE")
    print("=" * 80)

    db: Session = SessionLocal()

    test_emails = [
        "new_lab_applicant@aquawatch.ai",
        "hacker_tamper@aquawatch.ai",
        "pre_authorized_lab@aquawatch.ai",
        "test_normal_citizen@aquawatch.ai",
    ]

    try:
        # Pre-test cleanup
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.query(LabInvitation).filter(LabInvitation.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning during cleanup: {e}")

    results = {}

    # Seed normal citizen user into DB to test RBAC rejection
    normal_citizen = User(
        name="Citizen Tester",
        email="test_normal_citizen@aquawatch.ai",
        hashed_password=hash_password("CitizenPass123!"),
        role=UserRole.NORMAL_USER,
        is_active=True,
    )
    db.add(normal_citizen)
    db.commit()

    # -------------------------------------------------------------
    # 1. Signup API without invitation token
    # -------------------------------------------------------------
    print("\n--- Test 1: Lab Authority Signup Without Invitation Token ---")
    signup_payload = {
        "name": "Dr. Sarah Connor",
        "email": "new_lab_applicant@aquawatch.ai",
        "password": "LabPassword123!",
    }
    r_signup = client.post("/auth/register", json=signup_payload)
    if r_signup.status_code == 201:
        data = r_signup.json()
        assert data["email"] == "new_lab_applicant@aquawatch.ai"
        assert data["role"] == "LAB_AUTHORITY"
        assert data["is_active"] is False  # Pending admin approval
        results["1. Signup Without Token (HTTP 201)"] = "PASS"
        print(f"[PASS] Account '{data['email']}' created with role '{data['role']}' (Status: Pending Approval, is_active=False).")
    else:
        results["1. Signup Without Token (HTTP 201)"] = f"FAIL ({r_signup.status_code}: {r_signup.text})"
        print(f"[FAIL] {results['1. Signup Without Token (HTTP 201)']}")

    # -------------------------------------------------------------
    # 2. Client Role Tampering Blocked
    # -------------------------------------------------------------
    print("\n--- Test 2: Role Tampering Blocked (Client cannot choose role) ---")
    tamper_payload = {
        "name": "Tamper Test",
        "email": "hacker_tamper@aquawatch.ai",
        "password": "Password123!",
        "role": "SUPERUSER_ADMIN",
    }
    r_tamper = client.post("/auth/register", json=tamper_payload)
    if r_tamper.status_code == 201:
        tamper_data = r_tamper.json()
        assert tamper_data["role"] == "LAB_AUTHORITY"
        results["2. Role Tampering Blocked (Server Assigns Role)"] = "PASS"
        print("[PASS] Client role payload ignored. Role safely enforced as 'LAB_AUTHORITY' by backend.")
    else:
        results["2. Role Tampering Blocked (Server Assigns Role)"] = f"FAIL ({r_tamper.status_code})"
        print(f"[FAIL] {results['2. Role Tampering Blocked (Server Assigns Role)']}")

    # -------------------------------------------------------------
    # 3. Duplicate Email Rejection
    # -------------------------------------------------------------
    print("\n--- Test 3: Duplicate Email Registration Handling ---")
    r_dup = client.post("/auth/register", json=signup_payload)
    if r_dup.status_code == 400 and "already registered" in r_dup.text.lower():
        results["3. Duplicate Email Rejected (HTTP 400)"] = "PASS"
        print("[PASS] Duplicate registration rejected with HTTP 400 Bad Request.")
    else:
        results["3. Duplicate Email Rejected (HTTP 400)"] = f"FAIL ({r_dup.status_code}: {r_dup.text})"
        print(f"[FAIL] {results['3. Duplicate Email Rejected (HTTP 400)']}")

    # -------------------------------------------------------------
    # 4. Password Hashing Verification
    # -------------------------------------------------------------
    print("\n--- Test 4: Password Hashing Verification in Database ---")
    db_user = db.query(User).filter(User.email == "new_lab_applicant@aquawatch.ai").first()
    if db_user and db_user.hashed_password != "LabPassword123!" and "$argon2" in db_user.hashed_password:
        results["4. Password Safely Hashed (Argon2)"] = "PASS"
        print("[PASS] Plain password is never stored. Verified Argon2 password hash format.")
    else:
        results["4. Password Safely Hashed (Argon2)"] = "FAIL"
        print("[FAIL] Password hash verification failed.")

    # -------------------------------------------------------------
    # 5. Login Before Approval Blocked (403 Forbidden)
    # -------------------------------------------------------------
    print("\n--- Test 5: Login Attempt Before Administrator Approval ---")
    r_login_pre = client.post(
        "/auth/login",
        data={"username": "new_lab_applicant@aquawatch.ai", "password": "LabPassword123!"},
    )
    if r_login_pre.status_code == 403 and "approval" in r_login_pre.text.lower():
        results["5. Pre-Approval Login Blocked (HTTP 403)"] = "PASS"
        print("[PASS] Login before approval rejected with HTTP 403 Forbidden (Pending Approval).")
    else:
        results["5. Pre-Approval Login Blocked (HTTP 403)"] = f"FAIL ({r_login_pre.status_code}: {r_login_pre.text})"
        print(f"[FAIL] {results['5. Pre-Approval Login Blocked (HTTP 403)']}")

    # -------------------------------------------------------------
    # 6. Administrator Approval Workflow via CLI
    # -------------------------------------------------------------
    print("\n--- Test 6: Administrator Approval Workflow (assign_lab_authority.py --approve) ---")
    script_path = os.path.join(os.path.dirname(__file__), "assign_lab_authority.py")
    proc_approve = subprocess.run(
        [sys.executable, script_path, "--approve", "new_lab_applicant@aquawatch.ai"],
        capture_output=True,
        text=True,
    )
    if proc_approve.returncode == 0 and "successfully approved" in proc_approve.stdout.lower():
        db.expire_all()
        approved_user = db.query(User).filter(User.email == "new_lab_applicant@aquawatch.ai").first()
        assert approved_user.is_active is True
        assert approved_user.role == UserRole.LAB_AUTHORITY
        results["6. Administrative Approval CLI Workflow"] = "PASS"
        print(f"[PASS] Administrator successfully approved user via CLI. Account status is now active: {approved_user.is_active}")
    else:
        results["6. Administrative Approval CLI Workflow"] = f"FAIL ({proc_approve.returncode}: {proc_approve.stderr})"
        print(f"[FAIL] {results['6. Administrative Approval CLI Workflow']}")

    # -------------------------------------------------------------
    # 7. Login After Approval Produces JWT Bearer Token
    # -------------------------------------------------------------
    print("\n--- Test 7: Login After Administrator Approval ---")
    r_login_post = client.post(
        "/auth/login",
        data={"username": "new_lab_applicant@aquawatch.ai", "password": "LabPassword123!"},
    )
    if r_login_post.status_code == 200:
        lab_token = r_login_post.json().get("access_token")
        assert lab_token is not None
        results["7. Post-Approval Login Succeeds (HTTP 200)"] = "PASS"
        print("[PASS] Login succeeded with HTTP 200 OK. Bearer access token received.")
    else:
        results["7. Post-Approval Login Succeeds (HTTP 200)"] = f"FAIL ({r_login_post.status_code})"
        print(f"[FAIL] {results['7. Post-Approval Login Succeeds (HTTP 200)']}")
        lab_token = None

    # -------------------------------------------------------------
    # 8. Profile Inspection (/auth/me) with Bearer Token
    # -------------------------------------------------------------
    print("\n--- Test 8: Profile Inspection (/auth/me) ---")
    if lab_token:
        r_me = client.get("/auth/me", headers={"Authorization": f"Bearer {lab_token}"})
        if r_me.status_code == 200 and r_me.json().get("role") == "LAB_AUTHORITY":
            results["8. Verified Profile Role is LAB_AUTHORITY"] = "PASS"
            print(f"[PASS] /auth/me confirmed authenticated role: '{r_me.json().get('role')}', Email: '{r_me.json().get('email')}'.")
        else:
            results["8. Verified Profile Role is LAB_AUTHORITY"] = f"FAIL ({r_me.status_code})"
            print(f"[FAIL] {results['8. Verified Profile Role is LAB_AUTHORITY']}")
    else:
        results["8. Verified Profile Role is LAB_AUTHORITY"] = "SKIPPED"

    # -------------------------------------------------------------
    # 9. Protected Endpoints Enforce RBAC
    # -------------------------------------------------------------
    print("\n--- Test 9: Protected Endpoints Role Enforcement ---")
    # Unauthenticated request rejected with 401
    r_unauth = client.post("/water-quality", json={})
    assert r_unauth.status_code == 401, f"Expected 401, got {r_unauth.status_code}"

    # Normal user token rejected with 403 Forbidden
    norm_token, _ = create_access_token(data={"sub": "test_normal_citizen@aquawatch.ai", "role": "NORMAL_USER"})
    r_norm_post = client.get("/dashboard/official-summary", headers={"Authorization": f"Bearer {norm_token}"})
    assert r_norm_post.status_code == 403, f"Expected 403, got {r_norm_post.status_code}"

    # Lab authority token permitted with 200 OK
    if lab_token:
        r_lab_post = client.get("/dashboard/official-summary", headers={"Authorization": f"Bearer {lab_token}"})
        assert r_lab_post.status_code == 200, f"Expected 200, got {r_lab_post.status_code}"

    results["9. Protected Endpoints Enforce RBAC (401/403/200)"] = "PASS"
    print("[PASS] Unauthenticated (401), NORMAL_USER (403), and LAB_AUTHORITY (200) RBAC verified.")

    # -------------------------------------------------------------
    # 10. Public Endpoints Accessible Without Login
    # -------------------------------------------------------------
    print("\n--- Test 10: Public Endpoints Accessible Without Login ---")
    public_checks = [
        client.get("/"),
        client.get("/health"),
        client.get("/gis/locations"),
        client.get("/dashboard/summary"),
        client.get("/dashboard/water-quality-overview"),
        client.get("/dashboard/recent-measurements"),
        client.get("/water-quality/demo-samples"),
    ]
    if all(res.status_code == 200 for res in public_checks):
        results["10. Public Monitoring Endpoints Open (HTTP 200)"] = "PASS"
        print("[PASS] All public monitoring endpoints accessible without login.")
    else:
        results["10. Public Monitoring Endpoints Open (HTTP 200)"] = "FAIL"
        print("[FAIL] One or more public endpoints failed.")

    # -------------------------------------------------------------
    # 11. Pre-Authorized Email Signup
    # -------------------------------------------------------------
    print("\n--- Test 11: Pre-Authorized Email Signup (Auto-Activated) ---")
    pre_inv = LabInvitation(
        token_hash="preauth_hash_12345",
        email="pre_authorized_lab@aquawatch.ai",
        invited_by="admin@aquawatch.ai",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        is_used=False,
    )
    db.add(pre_inv)
    db.commit()

    r_preauth_signup = client.post(
        "/auth/register",
        json={
            "name": "Dr. Pre Authorized",
            "email": "pre_authorized_lab@aquawatch.ai",
            "password": "PreAuthPassword123!",
        },
    )
    if r_preauth_signup.status_code == 201 and r_preauth_signup.json().get("is_active") is True:
        results["11. Pre-Authorized Email Signup Immediately Active"] = "PASS"
        print("[PASS] Pre-authorized email registration automatically set is_active=True.")
    else:
        results["11. Pre-Authorized Email Signup Immediately Active"] = f"FAIL ({r_preauth_signup.status_code})"
        print(f"[FAIL] {results['11. Pre-Authorized Email Signup Immediately Active']}")

    # Cleanup test users
    try:
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.query(LabInvitation).filter(LabInvitation.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY:")
    all_passed = True
    for name, status_val in results.items():
        print(f"  {name:<60} : {status_val}")
        if status_val != "PASS":
            all_passed = False
    print("=" * 80)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
