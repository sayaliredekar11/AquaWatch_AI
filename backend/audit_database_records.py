"""
AquaWatch AI - Database Record Audit and Safe Cleanup Utility

Inspects PostgreSQL tables non-destructively:
- laboratories
- users
- water_bodies
- water_quality_records

Features:
1. --audit (default): Non-destructive audit reporting record counts and metadata.
2. --backup: Exports current tables to a timestamped JSON backup file.
3. --dry-run: Identifies records that lack laboratory accreditation or sample IDs.
4. --clean-test-runs: Safely removes ephemeral records from automated test runners (e.g. test_water_testing_v2),
   requiring explicit confirmation and automatic backup first. NEVER deletes genuine lab submissions.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Laboratory, User, WaterBody, WaterQualityRecord


def run_audit(db, verbose=False):
    print("=" * 70)
    print("AQUAWATCH AI - DATABASE RECORD AUDIT")
    print("=" * 70)

    # 1. Laboratories Audit
    total_labs = db.query(Laboratory).count()
    active_labs = db.query(Laboratory).filter(Laboratory.is_active == True).count()
    print(f"\n[1] LABORATORIES (Total: {total_labs}, Active: {active_labs})")
    labs = db.query(Laboratory).all()
    for lab in labs:
        print(f"  - ID: {lab.id} | License: {lab.license_number} | Status: {'ACTIVE' if lab.is_active else 'INACTIVE'}")
        print(f"    Name: {lab.name}")
        print(f"    Location: {lab.district}, {lab.state}")

    # 2. Users Audit
    total_users = db.query(User).count()
    lab_authorities = db.query(User).filter(User.role == "LAB_AUTHORITY").count()
    citizens = db.query(User).filter(User.role == "NORMAL_USER").count()
    print(f"\n[2] USERS (Total: {total_users} | Lab Authorities: {lab_authorities} | Citizens: {citizens})")
    users = db.query(User).all()
    for u in users:
        lic_str = f" | License: {u.laboratory_license_number}" if u.laboratory_license_number else ""
        print(f"  - User #{u.id}: {u.email} | Role: {u.role} | Active: {u.is_active}{lic_str}")

    # 3. Water Bodies Audit
    total_wb = db.query(WaterBody).count()
    print(f"\n[3] WATER BODIES / MONITORING LOCATIONS (Total: {total_wb})")
    water_bodies = db.query(WaterBody).all()
    for wb in water_bodies:
        rec_count = db.query(WaterQualityRecord).filter(WaterQualityRecord.water_body_id == wb.id).count()
        print(f"  - Location #{wb.id}: {wb.name}")
        print(f"    Type: {wb.water_body_type} | District: {wb.district or 'N/A'} | Coords: ({wb.latitude}, {wb.longitude}) | Tests: {rec_count}")

    # 4. Water Quality Records Audit
    total_records = db.query(WaterQualityRecord).count()
    records_with_reports = db.query(WaterQualityRecord).filter(WaterQualityRecord.report_id.isnot(None)).count()
    records_with_samples = db.query(WaterQualityRecord).filter(WaterQualityRecord.sample_id.isnot(None)).count()
    early_seed_records = db.query(WaterQualityRecord).filter(
        WaterQualityRecord.sample_id.is_(None),
        WaterQualityRecord.report_id.is_(None)
    ).count()

    print(f"\n[4] WATER QUALITY TESTING RECORDS (Total: {total_records})")
    print(f"  - Genuine Laboratory Submissions (with Sample ID): {records_with_samples}")
    print(f"  - Certified Reports Generated (with Report ID): {records_with_reports}")
    print(f"  - Legacy / Unattributed Early Test Records: {early_seed_records}")

    if verbose and total_records > 0:
        print("\nRecent 10 Records:")
        recent = db.query(WaterQualityRecord).order_by(WaterQualityRecord.id.desc()).limit(10).all()
        for r in recent:
            print(f"  * Rec #{r.id} | Sample: {r.sample_id or 'None'} | Report: {r.report_id or 'None'} | WQI: {r.wqi_score} | Category: {r.wqi_category} | Measured: {r.measured_at}")

    print("\n" + "=" * 70)
    print("Audit completed successfully. No records were modified.")
    print("=" * 70)


def backup_database(db, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(backup_dir, f"aquawatch_db_backup_{ts}.json")

    backup_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "laboratories": [
            {
                "id": l.id,
                "name": l.name,
                "license_number": l.license_number,
                "district": l.district,
                "state": l.state,
                "is_active": l.is_active,
            }
            for l in db.query(Laboratory).all()
        ],
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "role": str(u.role),
                "laboratory_id": u.laboratory_id,
                "laboratory_license_number": u.laboratory_license_number,
                "is_active": u.is_active,
            }
            for u in db.query(User).all()
        ],
        "water_bodies": [
            {
                "id": wb.id,
                "name": wb.name,
                "water_body_type": wb.water_body_type,
                "location_name": wb.location_name,
                "district": wb.district,
                "state": wb.state,
                "latitude": wb.latitude,
                "longitude": wb.longitude,
            }
            for wb in db.query(WaterBody).all()
        ],
        "water_quality_records": [
            {
                "id": r.id,
                "water_body_id": r.water_body_id,
                "sample_id": r.sample_id,
                "report_id": r.report_id,
                "sample_name": r.sample_name,
                "ph": r.ph,
                "dissolved_oxygen": r.dissolved_oxygen,
                "bod": r.bod,
                "cod": r.cod,
                "turbidity": r.turbidity,
                "tds": r.tds,
                "wqi_score": r.wqi_score,
                "wqi_category": r.wqi_category,
                "measured_at": r.measured_at.isoformat() if r.measured_at else None,
            }
            for r in db.query(WaterQualityRecord).all()
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2)

    print(f"[BACKUP SUCCESSFUL] Database state backed up to: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="AquaWatch AI Database Record Audit & Safe Management Utility")
    parser.add_argument("--audit", action="store_true", help="Perform non-destructive database audit (default)")
    parser.add_argument("--verbose", action="store_true", help="Include detailed record previews in audit")
    parser.add_argument("--backup", action="store_true", help="Create a JSON backup of database tables")

    args = parser.parse_args()
    db = SessionLocal()

    try:
        if args.backup:
            backup_database(db)
        # Default behavior is non-destructive audit
        run_audit(db, verbose=args.verbose)
    finally:
        db.close()


if __name__ == "__main__":
    main()
