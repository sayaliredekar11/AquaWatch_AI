"""
AquaWatch AI - Authentication & Authorization Verification Suite (Two Roles)

Verifies all 12 required testing scenarios for the simplified two-role system:
1. A new registration receives NORMAL_USER.
2. Registration cannot grant LAB_AUTHORITY by submitting a role field.
3. Duplicate email registration is rejected with HTTP 400.
4. Correct login credentials produce a valid token.
5. Incorrect credentials are rejected with HTTP 401.
6. Missing or invalid tokens receive HTTP 401.
7. A normal user can read permitted water-quality records / profile.
8. A normal user receives HTTP 403 when attempting a laboratory-only write operation.
9. A laboratory authority can perform permitted write operations.
10. Both roles can access their own authenticated profile.
11. No old role accidentally grants privileges (tokens with old role values receive 403 / 401).
12. Existing CRUD, GIS, dashboard, and authentication functionality continues to work.
"""

import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password, create_access_token

client = TestClient(app)


def run_all_tests():
    print("=" * 70)
    print("RUNNING AQUAWATCH AI TWO-ROLE AUTH & RBAC VERIFICATION SUITE")
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

    results = {}

    # -------------------------------------------------------------
    # Scenario 1: New registration receives NORMAL_USER
    # -------------------------------------------------------------
    reg_payload = {
        "name": "Alex Normal",
        "email": "test_normal@aquawatch.org",
        "password": "Password123!",
    }
    r = client.post("/auth/register", json=reg_payload)
    if r.status_code == 201 and r.json().get("role") == "NORMAL_USER" and "hashed_password" not in r.json():
        results["1. Registration Default Role is NORMAL_USER"] = "PASS"
        print("[PASS] Scenario 1: New user received NORMAL_USER as default role.")
    else:
        results["1. Registration Default Role is NORMAL_USER"] = f"FAIL ({r.status_code}, {r.text})"
        print(f"[FAIL] Scenario 1: {results['1. Registration Default Role is NORMAL_USER']}")

    # -------------------------------------------------------------
    # Scenario 2: Registration cannot grant LAB_AUTHORITY by submitting a role field
    # -------------------------------------------------------------
    hacker_payload = {
        "name": "Attacker Trying Lab Role",
        "email": "test_hacker@aquawatch.org",
        "password": "Password123!",
        "role": "LAB_AUTHORITY",
    }
    r = client.post("/auth/register", json=hacker_payload)
    if r.status_code == 201 and r.json().get("role") == "NORMAL_USER":
        results["2. Registration Role Tampering Blocked"] = "PASS"
        print("[PASS] Scenario 2: Client-supplied role was ignored; assigned NORMAL_USER.")
    else:
        results["2. Registration Role Tampering Blocked"] = f"FAIL (Assigned: {r.json().get('role')})"
        print(f"[FAIL] Scenario 2: {results['2. Registration Role Tampering Blocked']}")

    # -------------------------------------------------------------
    # Scenario 3: Duplicate email registration is rejected with HTTP 400
    # -------------------------------------------------------------
    r = client.post("/auth/register", json=reg_payload)
    if r.status_code == 400 and "already registered" in r.text.lower():
        results["3. Duplicate Email Rejection (400)"] = "PASS"
        print("[PASS] Scenario 3: Duplicate email was rejected with HTTP 400.")
    else:
        results["3. Duplicate Email Rejection (400)"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 3: {results['3. Duplicate Email Rejection (400)']}")

    # -------------------------------------------------------------
    # Scenario 4: Correct login credentials produce a valid token
    # -------------------------------------------------------------
    login_data = {
        "username": "test_normal@aquawatch.org",
        "password": "Password123!",
    }
    r = client.post("/auth/login", data=login_data)
    login_json = r.json()
    normal_token = login_json.get("access_token")
    if r.status_code == 200 and normal_token and login_json.get("token_type") == "bearer":
        results["4. Valid Login Produces Bearer Token"] = "PASS"
        print("[PASS] Scenario 4: Successful login returned valid Bearer access token.")
    else:
        results["4. Valid Login Produces Bearer Token"] = f"FAIL ({r.status_code})"
        print(f"[FAIL] Scenario 4: {results['4. Valid Login Produces Bearer Token']}")

    # -------------------------------------------------------------
    # Scenario 5: Incorrect credentials rejected with HTTP 401
    # -------------------------------------------------------------
    bad_login = {
        "username": "test_normal@aquawatch.org",
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

    # Create a laboratory user via administrative seeding
    lab_user = User(
        name="Dr. Lab Authority",
        email="test_lab@aquawatch.org",
        hashed_password=hash_password("LabSecret123!"),
        role=UserRole.LAB_AUTHORITY,
        is_active=True,
    )
    db.add(lab_user)
    db.commit()

    lab_login = client.post("/auth/login", data={"username": "test_lab@aquawatch.org", "password": "LabSecret123!"})
    lab_token = lab_login.json().get("access_token")

    normal_headers = {"Authorization": f"Bearer {normal_token}"}
    lab_headers = {"Authorization": f"Bearer {lab_token}"}

    # -------------------------------------------------------------
    # Scenario 7: Normal user can read permitted water-quality records
    # -------------------------------------------------------------
    r_read_wb = client.get("/water-bodies", headers=normal_headers)
    r_read_wq = client.get("/water-quality", headers=normal_headers)
    if r_read_wb.status_code == 200 and r_read_wq.status_code == 200:
        results["7. Normal User Reads Permitted Records"] = "PASS"
        print("[PASS] Scenario 7: NORMAL_USER successfully read water bodies and water quality records.")
    else:
        results["7. Normal User Reads Permitted Records"] = f"FAIL (WB: {r_read_wb.status_code}, WQ: {r_read_wq.status_code})"
        print(f"[FAIL] Scenario 7: {results['7. Normal User Reads Permitted Records']}")

    # -------------------------------------------------------------
    # Scenario 8: Normal user receives HTTP 403 on laboratory-only write operation
    # -------------------------------------------------------------
    wb_create_payload = {
        "name": "TEST_AUTH_Ganges",
        "water_body_type": "river",
        "location_name": "Test Location",
        "latitude": 25.3176,
        "longitude": 82.9739,
    }
    r_wb_write = client.post("/water-bodies", json=wb_create_payload, headers=normal_headers)
    r_lab_test = client.get("/auth/test/lab", headers=normal_headers)
    if r_wb_write.status_code == 403 and r_lab_test.status_code == 403:
        results["8. Normal User Blocked from Lab Writes (403)"] = "PASS"
        print("[PASS] Scenario 8: NORMAL_USER received HTTP 403 on laboratory write and test endpoints.")
    else:
        results["8. Normal User Blocked from Lab Writes (403)"] = f"FAIL (Write: {r_wb_write.status_code}, LabTest: {r_lab_test.status_code})"
        print(f"[FAIL] Scenario 8: {results['8. Normal User Blocked from Lab Writes (403)']}")

    # -------------------------------------------------------------
    # Scenario 9: Laboratory authority can perform permitted write operations
    # -------------------------------------------------------------
    r_lab_create = client.post("/water-bodies", json=wb_create_payload, headers=lab_headers)
    if r_lab_create.status_code == 201:
        created_wb_id = r_lab_create.json()["id"]
        # Create a water quality record as lab authority
        from datetime import datetime, timezone
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
    # Scenario 10: Both roles can access their own authenticated profile
    # -------------------------------------------------------------
    r_norm_me = client.get("/auth/me", headers=normal_headers)
    r_lab_me = client.get("/auth/me", headers=lab_headers)
    if (
        r_norm_me.status_code == 200
        and r_norm_me.json().get("role") == "NORMAL_USER"
        and r_lab_me.status_code == 200
        and r_lab_me.json().get("role") == "LAB_AUTHORITY"
    ):
        results["10. Both Roles Access Own Profile"] = "PASS"
        print("[PASS] Scenario 10: Both NORMAL_USER and LAB_AUTHORITY accessed their own profile.")
    else:
        results["10. Both Roles Access Own Profile"] = f"FAIL (Normal: {r_norm_me.status_code}, Lab: {r_lab_me.status_code})"
        print(f"[FAIL] Scenario 10: {results['10. Both Roles Access Own Profile']}")

    # -------------------------------------------------------------
    # Scenario 11: No old role accidentally grants privileges
    # -------------------------------------------------------------
    # Token with an obsolete role (e.g., 'ADMIN' or 'CITIZEN' or 'POLLUTION_OFFICIAL')
    obsolete_token_admin, _ = create_access_token(data={"sub": "test_normal@aquawatch.org", "role": "ADMIN"})
    # But database user has role NORMAL_USER, so checking against DB role rejects lab operations
    r_old_role = client.get("/auth/test/lab", headers={"Authorization": f"Bearer {obsolete_token_admin}"})
    if r_old_role.status_code == 403:
        results["11. Obsolete Roles Denied Privileges"] = "PASS"
        print("[PASS] Scenario 11: Old role references in tokens cannot access privileged lab endpoints (HTTP 403).")
    else:
        results["11. Obsolete Roles Denied Privileges"] = f"FAIL ({r_old_role.status_code})"
        print(f"[FAIL] Scenario 11: {results['11. Obsolete Roles Denied Privileges']}")

    # -------------------------------------------------------------
    # Scenario 12: Existing CRUD, GIS, dashboard, and authentication continue to work
    # -------------------------------------------------------------
    r_root = client.get("/")
    r_health = client.get("/health")
    r_health_db = client.get("/health/db")
    r_gis = client.get("/gis/locations")
    r_dash = client.get("/dashboard/summary")
    r_overview = client.get("/dashboard/water-quality-overview")

    if all(res.status_code == 200 for res in [r_root, r_health, r_health_db, r_gis, r_dash, r_overview]):
        results["12. Existing Foundation, GIS & Dashboards Intact"] = "PASS"
        print("[PASS] Scenario 12: Root, health, GIS locations, dashboard summary, and overview all operational (HTTP 200).")
    else:
        results["12. Existing Foundation, GIS & Dashboards Intact"] = "FAIL"
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
        print(f"  {test_name:<45} : {status_str}")
        if status_str != "PASS":
            all_passed = False
    print("=" * 70)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
