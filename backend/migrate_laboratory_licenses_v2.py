"""
AquaWatch AI - Database Migration: Laboratory Licenses Table & Foreign Key Association

This migration script safely:
1. Creates the `laboratory_licenses` table in PostgreSQL with:
   - id SERIAL PRIMARY KEY
   - license_number VARCHAR(100) UNIQUE NOT NULL
   - laboratory_name VARCHAR(200) NOT NULL
   - status VARCHAR(20) NOT NULL DEFAULT 'active' (active/inactive)
   - created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
2. Creates an index on `license_number`.
3. Seeds clearly identified demonstration/project laboratory licenses:
   - DEMO-LAB-2024-001 (AquaWatch Central Water Quality Laboratory) -> active
   - DEMO-LAB-2024-002 (Western Maharashtra Regional Testing Laboratory) -> active
   - DEMO-LAB-2024-003 (Krishna Basin Water Quality Testing Facility) -> active
   - DEMO-LAB-2024-004 (Panchganga River Monitoring Lab) -> active
   - DEMO-LAB-2024-005 (Urban Water Analysis Center) -> active
   - DEMO-LAB-INACTIVE-999 (Decommissioned Demonstration Water Lab) -> inactive
4. Migrates any existing records from `laboratories` into `laboratory_licenses` so
   historical licenses (e.g. MH-WAT-2024-001) remain 100% valid.
5. Updates the foreign key constraint on `users.laboratory_id` to reference `laboratory_licenses(id)`.
6. Does NOT drop, delete, or reset any existing user accounts or water quality records.
"""

import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.database import engine


def run_migration():
    print("=" * 75)
    print("AQUAWATCH AI - RUNNING LABORATORY LICENSES SCHEMA MIGRATION")
    print("=" * 75)

    with engine.begin() as conn:
        # 1. Create laboratory_licenses table
        print("[1/5] Creating 'laboratory_licenses' table if not exists...")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS laboratory_licenses (
                    id SERIAL PRIMARY KEY,
                    license_number VARCHAR(100) UNIQUE NOT NULL,
                    laboratory_name VARCHAR(200) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_laboratory_licenses_number 
                ON laboratory_licenses(license_number);
                """
            )
        )
        print("  -> Table 'laboratory_licenses' and index verified.")

        # 2. Seed approved academic demo laboratory licenses
        print("[2/5] Seeding academic demonstration laboratory registration IDs...")
        demo_licenses = [
            (
                "DEMO-LAB-2024-001",
                "AquaWatch Central Water Quality Laboratory",
                "active",
            ),
            (
                "DEMO-LAB-2024-002",
                "Western Maharashtra Regional Testing Laboratory",
                "active",
            ),
            (
                "DEMO-LAB-2024-003",
                "Krishna Basin Water Quality Testing Facility",
                "active",
            ),
            (
                "DEMO-LAB-2024-004",
                "Panchganga River Monitoring Lab",
                "active",
            ),
            (
                "DEMO-LAB-2024-005",
                "Urban Water Analysis Center",
                "active",
            ),
            (
                "DEMO-LAB-INACTIVE-999",
                "Decommissioned Demonstration Water Lab",
                "inactive",
            ),
        ]

        for lic_num, lab_name, status in demo_licenses:
            conn.execute(
                text(
                    """
                    INSERT INTO laboratory_licenses (license_number, laboratory_name, status)
                    VALUES (:license_number, :laboratory_name, :status)
                    ON CONFLICT (license_number) DO UPDATE SET
                        laboratory_name = EXCLUDED.laboratory_name,
                        status = EXCLUDED.status;
                    """
                ),
                {
                    "license_number": lic_num,
                    "laboratory_name": lab_name,
                    "status": status,
                },
            )
        print(f"  -> {len(demo_licenses)} demonstration laboratory licenses seeded.")

        # 3. Synchronize existing records from 'laboratories' into 'laboratory_licenses'
        print("[3/5] Syncing any existing 'laboratories' records into 'laboratory_licenses'...")
        existing_labs = conn.execute(
            text(
                """
                SELECT name, license_number, is_active FROM laboratories;
                """
            )
        ).fetchall()

        synced_count = 0
        for lab in existing_labs:
            lab_name = lab[0]
            lic_num = lab[1]
            status = "active" if lab[2] else "inactive"
            conn.execute(
                text(
                    """
                    INSERT INTO laboratory_licenses (license_number, laboratory_name, status)
                    VALUES (:license_number, :laboratory_name, :status)
                    ON CONFLICT (license_number) DO NOTHING;
                    """
                ),
                {
                    "license_number": lic_num,
                    "laboratory_name": lab_name,
                    "status": status,
                },
            )
            synced_count += 1
        print(f"  -> Synced {synced_count} existing records from 'laboratories'.")

        # 4. Update foreign key relationship on users table
        print("[4/5] Updating foreign key relationship on 'users' table...")
        # Check existing columns in users
        user_cols = {
            row[0]
            for row in conn.execute(
                text(
                    """
                    SELECT column_name FROM information_schema.columns WHERE table_name = 'users';
                    """
                )
            ).fetchall()
        }

        if "laboratory_id" not in user_cols:
            conn.execute(
                text(
                    """
                    ALTER TABLE users ADD COLUMN laboratory_id INTEGER;
                    """
                )
            )

        # Drop previous constraint if it points to laboratories
        conn.execute(
            text(
                """
                ALTER TABLE users DROP CONSTRAINT IF EXISTS users_laboratory_id_fkey;
                """
            )
        )

        # Add foreign key referencing laboratory_licenses(id)
        conn.execute(
            text(
                """
                ALTER TABLE users 
                ADD CONSTRAINT users_laboratory_id_fkey 
                FOREIGN KEY (laboratory_id) REFERENCES laboratory_licenses(id) ON DELETE SET NULL;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_users_laboratory_id ON users(laboratory_id);
                """
            )
        )
        print("  -> Foreign key 'users.laboratory_id' -> 'laboratory_licenses.id' established.")

        # 5. Verification
        total_licenses = conn.execute(
            text("SELECT COUNT(*) FROM laboratory_licenses;")
        ).scalar()
        active_licenses = conn.execute(
            text("SELECT COUNT(*) FROM laboratory_licenses WHERE status = 'active';")
        ).scalar()
        print(f"[5/5] Verification complete:")
        print(f"      Total laboratory licenses: {total_licenses}")
        print(f"      Active licenses:          {active_licenses}")

    print("=" * 75)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    run_migration()
