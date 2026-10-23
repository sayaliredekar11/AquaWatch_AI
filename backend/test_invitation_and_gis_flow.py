"""
AquaWatch AI - Comprehensive Invitation, Auth, RBAC & GIS Verification Suite

Covers user testing requirements G.1 to G.12:
1. Public pages and endpoints accessible without authentication
2. Normal user login/signup blocked
3. Lab Authority Signup & Login flow
4. Signup without invitation rejected (HTTP 403)
5. Signup with valid invitation creates LAB_AUTHORITY account (HTTP 201)
6. Expired or already-used invitation rejected (HTTP 400)
7. Email-restricted invitation enforced (HTTP 400)
8. New Lab Authority logs in successfully (HTTP 200)
9. Invalid credentials rejected (HTTP 401)
10. Unauthenticated requests to protected endpoints rejected (HTTP 401)
11. Non-Lab-Authority account blocked from protected endpoints (HTTP 403)
12. GIS demo stations & trend history endpoints functional (HTTP 200 & 404 on invalid)
"""

from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models import LabInvitation, User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password, create_access_token

client = TestClient(app)


def run_verification():
    print("=" * 75)
    print("AQUAWATCH AI — LAB AUTHORITY INVITATION & RBAC VERIFICATION SUITE")
    print("=" * 75)

    db: Session = SessionLocal()

    test_emails = [
        "invited_lab_user@aquawatch.ai",
        "restricted_lab_user@aquawatch.ai",
        "impostor_user@aquawatch.ai",
        "normal_db_user@aquawatch.ai",
        "active_lab_admin@aquawatch.ai",
    ]

    try:
        # Cleanup past test runs
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.query(LabInvitation).filter(
            (LabInvitation.invited_by.like("TEST_%")) | (LabInvitation.email.in_(test_emails))
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning during pre-test cleanup: {e}")

    # Seed baseline users
    # 1. Normal User (legacy or seeded in DB)
    normal_user = User(
        name="Normal Citizen",
        email="normal_db_user@aquawatch.ai",
        hashed_password=hash_password("CitizenPass123!"),
        role=UserRole.NORMAL_USER,
        is_active=True,
    )
    # 2. Existing Lab Authority Admin
    lab_admin = User(
        name="Dr. Lab Admin",
        email="active_lab_admin@aquawatch.ai",
        hashed_password=hash_password("AdminLabPass123!"),
        role=UserRole.LAB_AUTHORITY,
        is_active=True,
    )
    db.add(normal_user)
    db.add(lab_admin)
    db.commit()

    results = {}

    # -------------------------------------------------------------
    # 1. Public Endpoints Accessible Without Authentication
    # -------------------------------------------------------------
    print("\n--- 1. Testing Public Endpoints Without Auth ---")
    r_root = client.get("/")
    r_health = client.get("/health")
    r_gis = client.get("/gis/locations")
    r_demo1 = client.get("/gis/locations/demo_loc_001")
    r_demo1_hist = client.get("/gis/locations/demo_loc_001/history")
    r_summary = client.get("/dashboard/summary")
    r_overview = client.get("/dashboard/water-quality-overview")
    r_demo_samples = client.get("/water-quality/demo-samples")

    all_public_ok = (
        r_root.status_code == 200
        and r_health.status_code == 200
        and r_gis.status_code == 200
        and r_demo1.status_code == 200
        and r_demo1_hist.status_code == 200
        and r_summary.status_code == 200
        and r_overview.status_code == 200
        and r_demo_samples.status_code == 200
    )
    assert all_public_ok, "One or more public endpoints failed"
    results["1. Public Endpoints Accessible (HTTP 200)"] = "PASS"
    print("[PASS] Public endpoints (GIS, demo locations, history, dashboard summary, samples) open without login.")

    # -------------------------------------------------------------
    # 2. Normal User Login Is Blocked
    # -------------------------------------------------------------
    print("\n--- 2. Testing Normal User Login Restriction ---")
    r_norm_login = client.post(
        "/auth/login",
        data={"username": "normal_db_user@aquawatch.ai", "password": "CitizenPass123!"},
    )
    assert r_norm_login.status_code == 403, f"Expected 403, got {r_norm_login.status_code}"
    results["2. Normal User Login Blocked (HTTP 403)"] = "PASS"
    print("[PASS] Normal user login blocked with HTTP 403 Forbidden.")

    # -------------------------------------------------------------
    # 3. Lab Admin Generates Invitation Token
    # -------------------------------------------------------------
    print("\n--- 3. Testing Invitation Generation (Lab Authority Only) ---")
    # Log in as lab admin
    r_admin_login = client.post(
        "/auth/login",
        data={"username": "active_lab_admin@aquawatch.ai", "password": "AdminLabPass123!"},
    )
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Generate open invitation
    r_invite = client.post(
        "/auth/invitations",
        headers=admin_headers,
        json={"email": None, "expires_in_hours": 48},
    )
    assert r_invite.status_code == 201, f"Expected 201, got {r_invite.status_code}"
    invitation_token = r_invite.json()["invitation_token"]
    results["3. Lab Authority Creates Invitation (HTTP 201)"] = "PASS"
    print(f"[PASS] Successfully generated invitation token (Token: {invitation_token[:12]}...).")

    # -------------------------------------------------------------
    # 4. Pre-flight Validate Invitation Endpoint
    # -------------------------------------------------------------
    print("\n--- 4. Testing Invitation Pre-Flight Validation ---")
    r_val = client.get(f"/auth/invitations/validate?token={invitation_token}")
    assert r_val.status_code == 200
    assert r_val.json()["valid"] is True
    # Test invalid token
    r_val_bad = client.get("/auth/invitations/validate?token=bogus_token_123")
    assert r_val_bad.status_code == 200
    assert r_val_bad.json()["valid"] is False
    results["4. Invitation Pre-flight Validation"] = "PASS"
    print("[PASS] Token validation endpoint correctly verified valid and invalid tokens.")

    # -------------------------------------------------------------
    # 5. Signup Without Invitation Rejected
    # -------------------------------------------------------------
    print("\n--- 5. Testing Signup Without Invitation Token ---")
    r_no_tok = client.post(
        "/auth/register",
        json={
            "name": "Uninvited User",
            "email": "uninvited@aquawatch.ai",
            "password": "SecurePassword123!",
            "invitation_token": None,
        },
    )
    assert r_no_tok.status_code == 403, f"Expected 403, got {r_no_tok.status_code}"
    results["5. Uninvited Signup Rejected (HTTP 403)"] = "PASS"
    print("[PASS] Registration without invitation token rejected with HTTP 403 Forbidden.")

    # -------------------------------------------------------------
    # 6. Signup With Valid Invitation Creates LAB_AUTHORITY Account
    # -------------------------------------------------------------
    print("\n--- 6. Testing Valid Invitation Signup ---")
    r_reg = client.post(
        "/auth/register",
        json={
            "name": "Invited Lab Specialist",
            "email": "invited_lab_user@aquawatch.ai",
            "password": "LabSpecialist123!",
            "invitation_token": invitation_token,
        },
    )
    assert r_reg.status_code == 201, f"Expected 201, got {r_reg.status_code}: {r_reg.text}"
    user_data = r_reg.json()
    assert user_data["role"] == "LAB_AUTHORITY"
    results["6. Valid Invitation Creates LAB_AUTHORITY (HTTP 201)"] = "PASS"
    print(f"[PASS] Account '{user_data['email']}' successfully registered with server-enforced role 'LAB_AUTHORITY'.")

    # -------------------------------------------------------------
    # 7. Single-Use Enforcement: Reusing Token Fails
    # -------------------------------------------------------------
    print("\n--- 7. Testing Single-Use Token Enforcement ---")
    r_reuse = client.post(
        "/auth/register",
        json={
            "name": "Second User",
            "email": "second_user@aquawatch.ai",
            "password": "SecondPassword123!",
            "invitation_token": invitation_token,
        },
    )
    assert r_reuse.status_code == 400, f"Expected 400, got {r_reuse.status_code}"
    assert "already been used" in r_reuse.json()["detail"].lower()
    results["7. Reusing Token Blocked (HTTP 400)"] = "PASS"
    print("[PASS] Attempt to reuse already-consumed invitation token rejected with HTTP 400 Bad Request.")

    # -------------------------------------------------------------
    # 8. Expired Token Enforcement
    # -------------------------------------------------------------
    print("\n--- 8. Testing Expired Token Rejection ---")
    # Seed an expired token directly in DB
    raw_exp_token = "EXPIRED_" + secrets.token_urlsafe(24)
    exp_hash = hashlib.sha256(raw_exp_token.encode("utf-8")).hexdigest()
    now_utc = datetime.now(timezone.utc)
    expired_inv = LabInvitation(
        token_hash=exp_hash,
        email=None,
        invited_by="TEST_ADMIN",
        created_at=now_utc - timedelta(days=2),
        expires_at=now_utc - timedelta(hours=1),
        is_used=False,
    )
    db.add(expired_inv)
    db.commit()

    r_exp_reg = client.post(
        "/auth/register",
        json={
            "name": "Expired Attempt",
            "email": "expired_attempt@aquawatch.ai",
            "password": "ValidPassword123!",
            "invitation_token": raw_exp_token,
        },
    )
    assert r_exp_reg.status_code == 400, f"Expected 400, got {r_exp_reg.status_code}"
    assert "expired" in r_exp_reg.json()["detail"].lower()
    results["8. Expired Token Rejected (HTTP 400)"] = "PASS"
    print("[PASS] Expired invitation token rejected with HTTP 400 Bad Request.")

    # -------------------------------------------------------------
    # 9. Email-Restricted Invitation Enforcement
    # -------------------------------------------------------------
    print("\n--- 9. Testing Email-Restricted Invitation ---")
    r_rest_inv = client.post(
        "/auth/invitations",
        headers=admin_headers,
        json={"email": "restricted_lab_user@aquawatch.ai", "expires_in_hours": 48},
    )
    assert r_rest_inv.status_code == 201
    rest_token = r_rest_inv.json()["invitation_token"]

    # Try signing up with different email
    r_bad_email = client.post(
        "/auth/register",
        json={
            "name": "Impostor",
            "email": "impostor_user@aquawatch.ai",
            "password": "ImpostorPass123!",
            "invitation_token": rest_token,
        },
    )
    assert r_bad_email.status_code == 400
    assert "restricted" in r_bad_email.json()["detail"].lower()

    # Sign up with the designated email
    r_good_email = client.post(
        "/auth/register",
        json={
            "name": "Designated Specialist",
            "email": "restricted_lab_user@aquawatch.ai",
            "password": "DesignatedPass123!",
            "invitation_token": rest_token,
        },
    )
    assert r_good_email.status_code == 201
    results["9. Email Restriction Enforced (HTTP 400 & 201)"] = "PASS"
    print("[PASS] Email-restricted token rejected mismatched email and accepted designated email.")

    # -------------------------------------------------------------
    # 10. Login with Newly Created Lab Authority Account
    # -------------------------------------------------------------
    print("\n--- 10. Testing Login with New Lab Authority Account ---")
    r_new_login = client.post(
        "/auth/login",
        data={"username": "invited_lab_user@aquawatch.ai", "password": "LabSpecialist123!"},
    )
    assert r_new_login.status_code == 200
    new_token = r_new_login.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # Verify profile via /auth/me
    r_me = client.get("/auth/me", headers=new_headers)
    assert r_me.status_code == 200
    assert r_me.json()["role"] == "LAB_AUTHORITY"
    assert r_me.json()["email"] == "invited_lab_user@aquawatch.ai"
    results["10. New Lab Authority Login & Profile (HTTP 200)"] = "PASS"
    print("[PASS] New Lab Authority authenticated successfully; verified profile and role via /auth/me.")

    # -------------------------------------------------------------
    # 11. Invalid Credentials Rejection
    # -------------------------------------------------------------
    print("\n--- 11. Testing Bad Password & Nonexistent Email ---")
    r_bad_pw = client.post(
        "/auth/login",
        data={"username": "invited_lab_user@aquawatch.ai", "password": "WRONG_PASSWORD"},
    )
    assert r_bad_pw.status_code == 401
    r_no_user = client.post(
        "/auth/login",
        data={"username": "ghost@aquawatch.ai", "password": "AnyPassword123!"},
    )
    assert r_no_user.status_code == 401
    results["11. Bad Credentials Rejected (HTTP 401)"] = "PASS"
    print("[PASS] Invalid password and non-existent account rejected with HTTP 401 Unauthorized.")

    # -------------------------------------------------------------
    # 12. Protected Routes Role-Based Access Control
    # -------------------------------------------------------------
    print("\n--- 12. Testing Protected Endpoints (Test Water, Write, Dashboard) ---")
    # Unauthenticated
    r_unauth_test = client.post("/water-quality/test", json={"ph": 7.0, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0})
    assert r_unauth_test.status_code == 401

    # NORMAL_USER
    normal_token, _ = create_access_token(data={"sub": "normal_db_user@aquawatch.ai", "role": UserRole.NORMAL_USER.value})
    normal_headers = {"Authorization": f"Bearer {normal_token}"}
    r_norm_test = client.post("/water-quality/test", headers=normal_headers, json={"ph": 7.0, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0})
    assert r_norm_test.status_code == 403

    # LAB_AUTHORITY (newly registered user)
    r_lab_test = client.post(
        "/water-quality/test",
        headers=new_headers,
        json={"sample_name": "Lab Test", "ph": 7.2, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0},
    )
    assert r_lab_test.status_code == 200
    assert r_lab_test.json()["classification"] == "SAFE"

    # LAB_AUTHORITY dashboard official summary
    r_lab_dash = client.get("/dashboard/official-summary", headers=new_headers)
    assert r_lab_dash.status_code == 200

    results["12. Protected Routes RBAC (401 unauth / 403 normal / 200 lab)"] = "PASS"
    print("[PASS] Protected endpoints enforce RBAC: unauthenticated -> 401, NORMAL_USER -> 403, LAB_AUTHORITY -> 200.")

    # -------------------------------------------------------------
    # 13. GIS Station History & 404 for Unknown Locations
    # -------------------------------------------------------------
    print("\n--- 13. Testing GIS Locations & History Endpoints ---")
    r_locs = client.get("/gis/locations")
    assert r_locs.status_code == 200
    loc_items = r_locs.json()
    demo_ids = [l["location_id"] for l in loc_items if l.get("is_demo")]
    assert len(demo_ids) == 5, f"Expected 5 demo locations, got {len(demo_ids)}"

    # Test unknown station detail -> 404
    r_404_detail = client.get("/gis/locations/unknown_station_999")
    assert r_404_detail.status_code == 404

    # Test unknown station history -> 404
    r_404_hist = client.get("/gis/locations/unknown_station_999/history")
    assert r_404_hist.status_code == 404

    results["13. GIS Locations, 5 Demo Stations & 404 Handling"] = "PASS"
    print("[PASS] GIS returned 5 Maharashtra demo stations and returned HTTP 404 for nonexistent stations.")

    print("\n" + "=" * 75)
    print("ALL VERIFICATION SCENARIOS PASSED SUCCESSFULLY")
    print("=" * 75)
    for k, v in results.items():
        print(f"  {k:<55}: {v}")
    print("=" * 75)


if __name__ == "__main__":
    run_verification()
