"""
AquaWatch AI - Authentication & Authorization Verification Suite (Lab Authority Restriction)

Verifies all 12 testing scenarios for the Lab Authority only authentication model:
1. Public registration is disabled with HTTP 403 Forbidden.
2. Registration tampering is blocked with HTTP 403 Forbidden.
3. Normal users (NORMAL_USER in DB) cannot log in; rejected with HTTP 403 Forbidden.
4. Correct Lab Authority credentials produce a valid Bearer access token.
5. Incorrect credentials rejected with HTTP 401 Unauthorized.
6. Missing or invalid tokens receive HTTP 401 Unauthorized.
7. Public monitoring endpoints (GIS, dashboard summary, overview) are accessible without login.
8. Unauthenticated and non-lab requests to lab write/test endpoints receive 401 / 403.
9. A laboratory authority can perform permitted write operations.
10. Lab Authority can access its own authenticated profile (/auth/me).
11. Obsolete or tampered role tokens cannot access privileged endpoints.
12. Existing GIS, dashboard, and health checks continue to work.
"""

import sys
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password, create_access_token

client = TestClient(app)


def run_all_tests():
    print("=" * 70)
    print("RUNNING AQUAWATCH AI LAB AUTHORITY AUTH & RBAC VERIFICATION SUITE")
    print("=" * 70)

    db: Session = SessionLocal()

    test_emails = [
        "test_normal@aquawatch.org",
        "test_lab@aquawatch.org",
        "test_hacker@aquawatch.org",
        "test_legacy@aquawatch.org",
    ]

    # Clean up test user records from prior runs
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("TEST_AUTH_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("TEST_AUTH_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning during cleanup: {e}")

    # Seed an existing NORMAL_USER directly into DB to test that normal users cannot log in
    normal_user = User(
        name="Alex Normal",
        email="test_normal@aquawatch.org",
        hashed_password=hash_password("Password123!"),
        role=UserRole.NORMAL_USER,
        is_active=True,
    )
    # Seed an authorized LAB_AUTHORITY directly into DB (representing administrative provisioning)
    lab_user = User(
        name="Dr. Lab Authority",
        email="test_lab@aquawatch.org",
        hashed_password=hash_password("LabSecret123!"),
        role=UserRole.LAB_AUTHORITY,
        is_active=True,
    )
    db.add(normal_user)
    db.add(lab_user)
    db.commit()

    results = {}

    # -------------------------------------------------------------
    # Scenario 1: Public registration is disabled with HTTP 403
    # -------------------------------------------------------------
    reg_payload = {
        "name": "Jane Public",
        "email": "jane@aquawatch.org",
        "password": "Password123!",
    }
    r = client.post("/auth/register", json=reg_payload)
    if r.status_code == 403 and "disabled" in r.text.lower():
        results["1. Public Self-Registration Disabled (403)"] = "PASS"
        print("[PASS] Scenario 1: Public self-registration rejected with HTTP 403 Forbidden.")
    else:
        results["1. Public Self-Registration Disabled (403)"] = f"FAIL ({r.status_code}, {r.text})"
        print(f"[FAIL] Scenario 1: {results['1. Public Self-Registration Disabled (403)']}")

    # -------------------------------------------------------------
    # Scenario 2: Registration role tampering is blocked with HTTP 403
    # -------------------------------------------------------------
    hacker_payload = {
        "name": "Attacker Trying Lab Role",
        "email": "test_hacker@aquawatch.org",
        "password": "Password123!",
        "role": "LAB_AUTHORITY",
    }
    r = client.post("/auth/register", json=hacker_payload)
    if r.status_code == 403:
        results["2. Registration Role Tampering Blocked (403)"] = "PASS"
        print("[PASS] Scenario 2: Public registration tampering blocked with HTTP 403.")
    else:
        results["2. Registration Role Tampering Blocked (403)"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 2: {results['2. Registration Role Tampering Blocked (403)']}")

    # -------------------------------------------------------------
    # Scenario 3: Normal user login blocked with HTTP 403
    # -------------------------------------------------------------
    normal_login_data = {
        "username": "test_normal@aquawatch.org",
        "password": "Password123!",
    }
    r = client.post("/auth/login", data=normal_login_data)
    if r.status_code == 403 and "restricted" in r.text.lower():
        results["3. Normal User Login Blocked (403)"] = "PASS"
        print("[PASS] Scenario 3: Normal user login rejected with HTTP 403 Forbidden.")
    else:
        results["3. Normal User Login Blocked (403)"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 3: {results['3. Normal User Login Blocked (403)']}")

    # -------------------------------------------------------------
    # Scenario 4: Lab Authority login produces valid Bearer token
    # -------------------------------------------------------------
    lab_login_data = {
        "username": "test_lab@aquawatch.org",
        "password": "LabSecret123!",
    }
    r = client.post("/auth/login", data=lab_login_data)
    login_json = r.json()
    lab_token = login_json.get("access_token")
    if r.status_code == 200 and lab_token and login_json.get("token_type") == "bearer":
        results["4. Lab Authority Login Produces Bearer Token"] = "PASS"
        print("[PASS] Scenario 4: Lab Authority login returned valid Bearer access token.")
    else:
        results["4. Lab Authority Login Produces Bearer Token"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 4: {results['4. Lab Authority Login Produces Bearer Token']}")

    # -------------------------------------------------------------
    # Scenario 5: Incorrect credentials rejected with HTTP 401
    # -------------------------------------------------------------
    bad_login = {
        "username": "test_lab@aquawatch.org",
        "password": "WrongPassword999!",
    }
    r = client.post("/auth/login", data=bad_login)
    if r.status_code == 401 and "incorrect" in r.text.lower():
        results["5. Bad Password Rejection (401)"] = "PASS"
        print("[PASS] Scenario 5: Incorrect password rejected with HTTP 401.")
    else:
        results["5. Bad Password Rejection (401)"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 5: {results['5. Bad Password Rejection (401)']}")

    # -------------------------------------------------------------
    # Scenario 6: Missing or invalid tokens receive HTTP 401
    # -------------------------------------------------------------
    r_missing = client.get("/auth/me")
    r_invalid = client.get("/auth/me", headers={"Authorization": "Bearer not_a_valid_token_xyz"})
    if r_missing.status_code == 401 and r_invalid.status_code == 401:
        results["6. Missing/Invalid Token Rejected (401)"] = "PASS"
        print("[PASS] Scenario 6: Protected route rejected missing and invalid tokens with HTTP 401.")
    else:
        results["6. Missing/Invalid Token Rejected (401)"] = f"FAIL (Missing: {r_missing.status_code}, Invalid: {r_invalid.status_code})"
        print(f"[FAIL] Scenario 6: {results['6. Missing/Invalid Token Rejected (401)']}")

    lab_headers = {"Authorization": f"Bearer {lab_token}"}
    # Create a synthetic token for normal user to test backend RBAC defenses
    normal_token, _ = create_access_token(data={"sub": "test_normal@aquawatch.org", "role": "NORMAL_USER"})
    normal_headers = {"Authorization": f"Bearer {normal_token}"}

    # -------------------------------------------------------------
    # Scenario 7: Public monitoring endpoints accessible without login
    # -------------------------------------------------------------
    r_gis = client.get("/gis/locations")
    r_dash = client.get("/dashboard/summary")
    r_overview = client.get("/dashboard/water-quality-overview")
    r_recent = client.get("/dashboard/recent-measurements")
    if all(res.status_code == 200 for res in [r_gis, r_dash, r_overview, r_recent]):
        results["7. Public Monitoring Views Accessible (200)"] = "PASS"
        print("[PASS] Scenario 7: GIS, summary, overview, and recents accessible without auth.")
    else:
        results["7. Public Monitoring Views Accessible (200)"] = "FAIL"
        print(f"[FAIL] Scenario 7: Public views failed unauthenticated access.")

    # -------------------------------------------------------------
    # Scenario 8: Non-lab & unauthenticated requests blocked from lab endpoints
    # -------------------------------------------------------------
    wb_create_payload = {
        "name": "TEST_AUTH_Ganges",
        "water_body_type": "river",
        "location_name": "Test Location",
        "latitude": 25.3176,
        "longitude": 82.9739,
    }
    r_unauth_write = client.post("/water-bodies", json=wb_create_payload)
    r_norm_write = client.post("/water-bodies", json=wb_create_payload, headers=normal_headers)
    r_norm_test = client.post("/water-quality/test", json={"sample_name": "Test", "ph": 7.0, "dissolved_oxygen": 7.0, "bod": 2.0, "turbidity": 3.0, "tds": 250.0}, headers=normal_headers)
    if r_unauth_write.status_code == 401 and r_norm_write.status_code == 403 and r_norm_test.status_code == 403:
        results["8. Non-Lab Blocked from Writes/Tests (401/403)"] = "PASS"
        print("[PASS] Scenario 8: Unauthenticated returned 401, NORMAL_USER returned 403 on lab endpoints.")
    else:
        results["8. Non-Lab Blocked from Writes/Tests (401/403)"] = f"FAIL (Unauth: {r_unauth_write.status_code}, NormWrite: {r_norm_write.status_code}, NormTest: {r_norm_test.status_code})"
        print(f"[FAIL] Scenario 8: {results['8. Non-Lab Blocked from Writes/Tests (401/403)']}")

    # -------------------------------------------------------------
    # Scenario 9: Laboratory authority can perform permitted write operations
    # -------------------------------------------------------------
    r_lab_create = client.post("/water-bodies", json=wb_create_payload, headers=lab_headers)
    if r_lab_create.status_code == 201:
        created_wb_id = r_lab_create.json()["id"]
        wq_payload = {
            "water_body_id": created_wb_id,
            "ph": 7.4,
            "dissolved_oxygen": 6.8,
            "bod": 2.2,
            "turbidity": 4.1,
            "tds": 240.0,
            "measured_at": datetime.now(timezone.utc).isoformat(),
        }
        r_wq_create = client.post("/water-quality", json=wq_payload, headers=lab_headers)
        if r_wq_create.status_code == 201:
            results["9. Lab Authority Performs Permitted Writes"] = "PASS"
            print("[PASS] Scenario 9: LAB_AUTHORITY successfully created water body and water quality record.")
        else:
            results["9. Lab Authority Performs Permitted Writes"] = f"FAIL (WQ Write: {r_wq_create.status_code})"
            print(f"[FAIL] Scenario 9: {results['9. Lab Authority Performs Permitted Writes']}")
    else:
        results["9. Lab Authority Performs Permitted Writes"] = f"FAIL (WB Write: {r_lab_create.status_code})"
        print(f"[FAIL] Scenario 9: {results['9. Lab Authority Performs Permitted Writes']}")

    # -------------------------------------------------------------
    # Scenario 10: Lab Authority can access its own authenticated profile
    # -------------------------------------------------------------
    r_lab_me = client.get("/auth/me", headers=lab_headers)
    if r_lab_me.status_code == 200 and r_lab_me.json().get("role") == "LAB_AUTHORITY":
        results["10. Lab Authority Profile Access (/auth/me)"] = "PASS"
        print("[PASS] Scenario 10: LAB_AUTHORITY successfully accessed own profile.")
    else:
        results["10. Lab Authority Profile Access (/auth/me)"] = f"FAIL (Lab: {r_lab_me.status_code})"
        print(f"[FAIL] Scenario 10: {results['10. Lab Authority Profile Access (/auth/me)']}")

    # -------------------------------------------------------------
    # Scenario 11: Obsolete or tampered roles denied privileges
    # -------------------------------------------------------------
    obsolete_token_admin, _ = create_access_token(data={"sub": "test_normal@aquawatch.org", "role": "ADMIN"})
    r_old_role = client.get("/auth/test/lab", headers={"Authorization": f"Bearer {obsolete_token_admin}"})
    if r_old_role.status_code == 403:
        results["11. Obsolete Roles Denied Privileges (403)"] = "PASS"
        print("[PASS] Scenario 11: Old role references in tokens cannot access privileged lab endpoints (HTTP 403).")
    else:
        results["11. Obsolete Roles Denied Privileges (403)"] = f"FAIL ({r_old_role.status_code})"
        print(f"[FAIL] Scenario 11: {results['11. Obsolete Roles Denied Privileges (403)']}")

    # -------------------------------------------------------------
    # Scenario 12: Existing foundation endpoints continue to work
    # -------------------------------------------------------------
    r_root = client.get("/")
    r_health = client.get("/health")
    r_health_db = client.get("/health/db")

    if all(res.status_code == 200 for res in [r_root, r_health, r_health_db]):
        results["12. Existing Foundation Endpoints Intact (200)"] = "PASS"
        print("[PASS] Scenario 12: Root, health, and health/db operational (HTTP 200).")
    else:
        results["12. Existing Foundation Endpoints Intact (200)"] = "FAIL"
        print(f"[FAIL] Scenario 12: Foundation endpoints degraded.")

    # Cleanup test records
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("TEST_AUTH_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("TEST_AUTH_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()

    db.close()

    print("=" * 70)
    print("FINAL TEST SUMMARY:")
    all_passed = True
    for test_name, status_str in results.items():
        print(f"  {test_name:<48} : {status_str}")
        if status_str != "PASS":
            all_passed = False
    print("=" * 70)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
