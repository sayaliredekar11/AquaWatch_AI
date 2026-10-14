"""
AquaWatch AI - Day 3 Water Quality Management Test Suite (Two-Role Schema)

Verifies Day 3 scenarios with NORMAL_USER and LAB_AUTHORITY:
1. LAB_AUTHORITY creates water body (POST /water-bodies)
2. NORMAL_USER cannot create water body (403 Forbidden)
3. Both roles can list water bodies (GET /water-bodies)
4. Nonexistent water body returns 404 Not Found
5. LAB_AUTHORITY creates measurement record (POST /water-quality)
6. Creating measurement for nonexistent water body returns 404 Not Found
7. Invalid pH is rejected (422)
8. Negative measurement values are rejected (422)
9. Optional measurement fields can be omitted / null
10. Pagination and filtering work (skip, limit, water_body_id, date range)
11. LAB_AUTHORITY updates existing record (PATCH)
12. PATCH changes only supplied fields
13. NORMAL_USER cannot update or delete records (403 Forbidden)
14. Record deletion is restricted under two-role policy (403 Forbidden)
15. Water body deletion is restricted under two-role policy (403 Forbidden)
16. Day 1 & Day 2 foundation endpoints remain operational
"""

import sys
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password, create_access_token

client = TestClient(app)


def run_day3_tests():
    print("=" * 70)
    print("RUNNING AQUAWATCH AI DAY 3 WATER QUALITY CRUD & RBAC TEST SUITE")
    print("=" * 70)

    db: Session = SessionLocal()

    test_emails = [
        "day3_normal@aquawatch.org",
        "day3_lab@aquawatch.org",
    ]

    # Clean existing test data from previous runs
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("TEST_D3_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("TEST_D3_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning during initial cleanup: {e}")

    # Seed users
    users = {
        "normal": User(
            name="Test Normal User",
            email="day3_normal@aquawatch.org",
            hashed_password=hash_password("Password123!"),
            role=UserRole.NORMAL_USER,
            is_active=True,
        ),
        "lab": User(
            name="Test Lab Analyst",
            email="day3_lab@aquawatch.org",
            hashed_password=hash_password("Password123!"),
            role=UserRole.LAB_AUTHORITY,
            is_active=True,
        ),
    }
    db.add_all(list(users.values()))
    db.commit()

    # Generate Bearer tokens
    tokens = {
        role: create_access_token(data={"sub": u.email, "role": u.role.value})[0]
        for role, u in users.items()
    }
    headers = {role: {"Authorization": f"Bearer {t}"} for role, t in tokens.items()}

    results = {}

    # -------------------------------------------------------------
    # Scenario 1: LAB_AUTHORITY can create a water body
    # -------------------------------------------------------------
    wb_payload = {
        "name": "TEST_D3_Ganges_Haridwar",
        "water_body_type": "river",
        "location_name": "Haridwar Upper Ghat",
        "latitude": 29.9457,
        "longitude": 78.1642,
    }
    r = client.post("/water-bodies", json=wb_payload, headers=headers["lab"])
    if r.status_code == 201 and r.json().get("name") == wb_payload["name"]:
        created_wb_id = r.json()["id"]
        results["1. Authorized Water Body Creation"] = "PASS"
        print("[PASS] Scenario 1: LAB_AUTHORITY created a water body successfully.")
    else:
        created_wb_id = None
        results["1. Authorized Water Body Creation"] = f"FAIL (Status {r.status_code}, Body: {r.text})"
        print(f"[FAIL] Scenario 1: {results['1. Authorized Water Body Creation']}")

    # -------------------------------------------------------------
    # Scenario 2: NORMAL_USER cannot create a water body (403)
    # -------------------------------------------------------------
    r = client.post("/water-bodies", json=wb_payload, headers=headers["normal"])
    if r.status_code == 403:
        results["2. Normal User Water Body Creation Blocked"] = "PASS"
        print("[PASS] Scenario 2: NORMAL_USER blocked with HTTP 403 Forbidden.")
    else:
        results["2. Normal User Water Body Creation Blocked"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 2: {results['2. Normal User Water Body Creation Blocked']}")

    # -------------------------------------------------------------
    # Scenario 3: Authenticated user can list water bodies
    # -------------------------------------------------------------
    r = client.get("/water-bodies?skip=0&limit=10", headers=headers["normal"])
    if r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) >= 1:
        results["3. List Water Bodies"] = "PASS"
        print("[PASS] Scenario 3: Listed water bodies with pagination successfully.")
    else:
        results["3. List Water Bodies"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 3: {results['3. List Water Bodies']}")

    # -------------------------------------------------------------
    # Scenario 4: Nonexistent water body returns 404
    # -------------------------------------------------------------
    r = client.get("/water-bodies/999999", headers=headers["normal"])
    if r.status_code == 404:
        results["4. Nonexistent Water Body 404"] = "PASS"
        print("[PASS] Scenario 4: Nonexistent water body returned HTTP 404.")
    else:
        results["4. Nonexistent Water Body 404"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 4: {results['4. Nonexistent Water Body 404']}")

    # -------------------------------------------------------------
    # Scenario 5: LAB_AUTHORITY creates measurement record
    # -------------------------------------------------------------
    now_utc = datetime.now(timezone.utc)
    rec_payload = {
        "water_body_id": created_wb_id,
        "ph": 7.4,
        "dissolved_oxygen": 6.8,
        "bod": 2.1,
        "turbidity": 4.5,
        "tds": 240.0,
        "electrical_conductivity": 350.0,
        "nitrate": 1.2,
        "temperature": 21.5,
        "measured_at": now_utc.isoformat(),
    }
    r = client.post("/water-quality", json=rec_payload, headers=headers["lab"])
    if r.status_code == 201 and r.json().get("water_body_id") == created_wb_id:
        created_rec_id = r.json()["id"]
        results["5. Create Measurement Record"] = "PASS"
        print("[PASS] Scenario 5: Measurement record created successfully.")
    else:
        created_rec_id = None
        results["5. Create Measurement Record"] = f"FAIL (Status {r.status_code}, Body: {r.text})"
        print(f"[FAIL] Scenario 5: {results['5. Create Measurement Record']}")

    # -------------------------------------------------------------
    # Scenario 6: Nonexistent water_body_id returns 404
    # -------------------------------------------------------------
    bad_fk_payload = rec_payload.copy()
    bad_fk_payload["water_body_id"] = 999999
    r = client.post("/water-quality", json=bad_fk_payload, headers=headers["lab"])
    if r.status_code == 404:
        results["6. Invalid Water Body ID 404"] = "PASS"
        print("[PASS] Scenario 6: Nonexistent water_body_id rejected with HTTP 404.")
    else:
        results["6. Invalid Water Body ID 404"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 6: {results['6. Invalid Water Body ID 404']}")

    # -------------------------------------------------------------
    # Scenario 7: Out-of-bounds pH rejected (422)
    # -------------------------------------------------------------
    bad_ph_low = rec_payload.copy()
    bad_ph_low["ph"] = -0.5
    r_low = client.post("/water-quality", json=bad_ph_low, headers=headers["lab"])
    bad_ph_high = rec_payload.copy()
    bad_ph_high["ph"] = 15.2
    r_high = client.post("/water-quality", json=bad_ph_high, headers=headers["lab"])
    if r_low.status_code == 422 and r_high.status_code == 422:
        results["7. Invalid pH Rejection"] = "PASS"
        print("[PASS] Scenario 7: Out-of-bounds pH values (-0.5 and 15.2) rejected with HTTP 422.")
    else:
        results["7. Invalid pH Rejection"] = f"FAIL (Low: {r_low.status_code}, High: {r_high.status_code})"
        print(f"[FAIL] Scenario 7: {results['7. Invalid pH Rejection']}")

    # -------------------------------------------------------------
    # Scenario 8: Negative measurements rejected (422)
    # -------------------------------------------------------------
    bad_neg = rec_payload.copy()
    bad_neg["dissolved_oxygen"] = -1.0
    r_neg = client.post("/water-quality", json=bad_neg, headers=headers["lab"])
    if r_neg.status_code == 422:
        results["8. Negative Measurements Rejection"] = "PASS"
        print("[PASS] Scenario 8: Negative measurements (DO) rejected with HTTP 422.")
    else:
        results["8. Negative Measurements Rejection"] = f"FAIL (Status {r_neg.status_code})"
        print(f"[FAIL] Scenario 8: {results['8. Negative Measurements Rejection']}")

    # -------------------------------------------------------------
    # Scenario 9: Optional fields can be omitted or null
    # -------------------------------------------------------------
    sparse_payload = {
        "water_body_id": created_wb_id,
        "ph": 7.1,
        "dissolved_oxygen": None,
        "measured_at": now_utc.isoformat(),
    }
    r = client.post("/water-quality", json=sparse_payload, headers=headers["lab"])
    if r.status_code == 201 and r.json().get("dissolved_oxygen") is None and r.json().get("bod") is None:
        results["9. Nullable & Omitted Optional Fields"] = "PASS"
        print("[PASS] Scenario 9: Measurement created with omitted/null optional parameters.")
    else:
        results["9. Nullable & Omitted Optional Fields"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 9: {results['9. Nullable & Omitted Optional Fields']}")

    # -------------------------------------------------------------
    # Scenario 10: Pagination and filtering work
    # -------------------------------------------------------------
    start_filter = (now_utc - timedelta(hours=1)).isoformat()
    end_filter = (now_utc + timedelta(hours=1)).isoformat()
    r = client.get(
        "/water-quality",
        params={
            "water_body_id": created_wb_id,
            "start_date": start_filter,
            "end_date": end_filter,
            "skip": 0,
            "limit": 5,
        },
        headers=headers["normal"],
    )
    if r.status_code == 200 and len(r.json()) >= 1 and r.json()[0]["water_body_id"] == created_wb_id:
        results["10. Pagination & Filtering"] = "PASS"
        print("[PASS] Scenario 10: Filtered measurements by water_body_id and date range.")
    else:
        results["10. Pagination & Filtering"] = f"FAIL (Status {r.status_code})"
        print(f"[FAIL] Scenario 10: {results['10. Pagination & Filtering']}")

    # -------------------------------------------------------------
    # Scenario 11 & 12: LAB_AUTHORITY updates record via PATCH
    # -------------------------------------------------------------
    patch_payload = {"ph": 8.1}
    r = client.patch(f"/water-quality/{created_rec_id}", json=patch_payload, headers=headers["lab"])
    patch_json = r.json()
    if (
        r.status_code == 200
        and patch_json.get("ph") == 8.1
        and patch_json.get("dissolved_oxygen") == 6.8
    ):
        results["11. Authorized PATCH Update"] = "PASS"
        results["12. Partial Update Integrity"] = "PASS"
        print("[PASS] Scenario 11 & 12: PATCH updated pH to 8.1 while preserving other fields.")
    else:
        results["11. Authorized PATCH Update"] = f"FAIL (Status {r.status_code})"
        results["12. Partial Update Integrity"] = "FAIL"
        print(f"[FAIL] Scenario 11 & 12: {results['11. Authorized PATCH Update']}")

    # -------------------------------------------------------------
    # Scenario 13: NORMAL_USER cannot update or delete records (403)
    # -------------------------------------------------------------
    r_patch_norm = client.patch(f"/water-quality/{created_rec_id}", json={"ph": 7.0}, headers=headers["normal"])
    r_del_norm = client.delete(f"/water-quality/{created_rec_id}", headers=headers["normal"])
    if r_patch_norm.status_code == 403 and r_del_norm.status_code == 403:
        results["13. Unauthorized Write Blocked (403)"] = "PASS"
        print("[PASS] Scenario 13: NORMAL_USER blocked with HTTP 403 on PATCH and DELETE.")
    else:
        results["13. Unauthorized Write Blocked (403)"] = f"FAIL (Patch: {r_patch_norm.status_code}, Del: {r_del_norm.status_code})"
        print(f"[FAIL] Scenario 13: {results['13. Unauthorized Write Blocked (403)']}")

    # -------------------------------------------------------------
    # Scenario 14: Record deletion is restricted under two-role policy (403)
    # -------------------------------------------------------------
    r_del_lab = client.delete(f"/water-quality/{created_rec_id}", headers=headers["lab"])
    if r_del_lab.status_code == 403:
        results["14. Record Deletion Restricted (403)"] = "PASS"
        print("[PASS] Scenario 14: Record deletion is restricted under two-role policy (HTTP 403).")
    else:
        results["14. Record Deletion Restricted (403)"] = f"FAIL (Status {r_del_lab.status_code})"
        print(f"[FAIL] Scenario 14: {results['14. Record Deletion Restricted (403)']}")

    # -------------------------------------------------------------
    # Scenario 15: Water body deletion is restricted under two-role policy (403)
    # -------------------------------------------------------------
    r_wb_del = client.delete(f"/water-bodies/{created_wb_id}", headers=headers["lab"])
    if r_wb_del.status_code == 403:
        results["15. Water Body Deletion Restricted (403)"] = "PASS"
        print("[PASS] Scenario 15: Water body deletion is restricted under two-role policy (HTTP 403).")
    else:
        results["15. Water Body Deletion Restricted (403)"] = f"FAIL (Status {r_wb_del.status_code})"
        print(f"[FAIL] Scenario 15: {results['15. Water Body Deletion Restricted (403)']}")

    # -------------------------------------------------------------
    # Scenario 16: Day 1 & Day 2 foundation endpoints remain operational
    # -------------------------------------------------------------
    r_root = client.get("/")
    r_health = client.get("/health")
    r_health_db = client.get("/health/db")
    r_me = client.get("/auth/me", headers=headers["normal"])
    if all(res.status_code == 200 for res in [r_root, r_health, r_health_db, r_me]):
        results["16. Day 1 & Day 2 Endpoints Operational"] = "PASS"
        print("[PASS] Scenario 16: Day 1 (/health, /health/db) and Day 2 (/auth/me) fully operational.")
    else:
        results["16. Day 1 & Day 2 Endpoints Operational"] = "FAIL"
        print(f"[FAIL] Scenario 16: Foundation endpoints degraded.")

    # Cleanup test records
    try:
        db.query(WaterQualityRecord).filter(
            WaterQualityRecord.water_body.has(WaterBody.name.like("TEST_D3_%"))
        ).delete(synchronize_session=False)
        db.query(WaterBody).filter(WaterBody.name.like("TEST_D3_%")).delete(synchronize_session=False)
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
    run_day3_tests()
