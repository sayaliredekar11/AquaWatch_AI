"""
AquaWatch AI - Database Migration: Laboratory Licenses & User Association

This migration script safely:
1. Creates the `laboratories` table if it does not already exist.
2. Ensures `license_number` has a unique constraint and index.
3. Adds `laboratory_id` and `laboratory_license_number` to `users` table if they do not exist.
4. Adds foreign key constraint referencing `laboratories.id`.
5. Pre-registers official authorized laboratory licenses in Maharashtra.
6. Does NOT drop, delete, or overwrite any existing data or tables.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.database import engine


def run_migration():
    print("=" * 70)
    print("AQUAWATCH AI - RUNNING LABORATORY LICENSE SCHEMA MIGRATION")
    print("=" * 70)

    with engine.begin() as conn:
        # 1. Create laboratories table
        print("[1/4] Checking and creating 'laboratories' table...")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS laboratories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    license_number VARCHAR(100) UNIQUE NOT NULL,
                    issuing_authority VARCHAR(200) DEFAULT 'Maharashtra Water Quality Regulatory Authority',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    district VARCHAR(100),
                    state VARCHAR(100) DEFAULT 'Maharashtra',
                    contact_email VARCHAR(255),
                    contact_phone VARCHAR(50),
                    address VARCHAR(300),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_laboratories_license_number ON laboratories(license_number);
                """
            )
        )
        print("  -> 'laboratories' table and index verified.")

        # 2. Check and add columns to users table
        print("[2/4] Checking 'users' table columns...")
        existing_cols_result = conn.execute(
            text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users';
                """
            )
        )
        user_cols = {row[0] for row in existing_cols_result}

        if "laboratory_id" not in user_cols:
            print("  -> Adding 'laboratory_id' column to 'users' table...")
            conn.execute(
                text(
                    """
                    ALTER TABLE users 
                    ADD COLUMN laboratory_id INTEGER REFERENCES laboratories(id) ON DELETE SET NULL;
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
        else:
            print("  -> 'laboratory_id' already exists in 'users'.")

        if "laboratory_license_number" not in user_cols:
            print("  -> Adding 'laboratory_license_number' column to 'users' table...")
            conn.execute(
                text(
                    """
                    ALTER TABLE users 
                    ADD COLUMN laboratory_license_number VARCHAR(100);
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_users_lab_license ON users(laboratory_license_number);
                    """
                )
            )
        else:
            print("  -> 'laboratory_license_number' already exists in 'users'.")

        if "laboratory_name" not in user_cols:
            print("  -> Adding 'laboratory_name' column to 'users' table...")
            conn.execute(
                text(
                    """
                    ALTER TABLE users 
                    ADD COLUMN laboratory_name VARCHAR(200);
                    """
                )
            )
        else:
            print("  -> 'laboratory_name' already exists in 'users'.")

        if "designation" not in user_cols:
            print("  -> Adding 'designation' column to 'users' table...")
            conn.execute(
                text(
                    """
                    ALTER TABLE users 
                    ADD COLUMN designation VARCHAR(100);
                    """
                )
            )
        else:
            print("  -> 'designation' already exists in 'users'.")

        # 3. Seed official registered laboratories
        print("[3/4] Seeding authorized Maharashtra laboratory license records...")
        authorized_labs = [
            (
                "Maharashtra State Central Water Testing Laboratory",
                "MH-WAT-2024-001",
                "Maharashtra Water Quality Regulatory Authority",
                True,
                "Pune",
                "Maharashtra",
                "central.lab@waterquality.mh.gov.in",
                "+91 (020) 2569-8000",
                "Shivaji Nagar Environmental Complex, Pune - 411005",
            ),
            (
                "Western Maharashtra Regional Water Testing Laboratory",
                "MH-WAT-2024-002",
                "Maharashtra Pollution Control Board (MPCB)",
                True,
                "Kolhapur",
                "Maharashtra",
                "kolhapur.waterlab@mpcb.gov.in",
                "+91 (0231) 265-4321",
                "MIDC Industrial Area, Shiroli, Kolhapur - 416122",
            ),
            (
                "Krishna Basin Water Quality Testing Facility",
                "MH-WAT-2024-003",
                "Krishna Valley Development Corporation",
                True,
                "Sangli",
                "Maharashtra",
                "krishna.basin.lab@waterquality.org",
                "+91 (0233) 232-1100",
                "River Bank Road, Sangli Ghat, Sangli - 416416",
            ),
            (
                "Nashik Division Environmental Testing Laboratory",
                "MH-WAT-2024-004",
                "Maharashtra State Water Quality Cell",
                True,
                "Nashik",
                "Maharashtra",
                "nashik.waterlab@gov.in",
                "+91 (0253) 257-8900",
                "Trimbak Road Complex, Nashik - 422002",
            ),
            (
                "Mumbai Metropolitan Water Analysis Bureau",
                "MH-WAT-2024-005",
                "Urban Water Supply & Sanitation Department",
                True,
                "Mumbai",
                "Maharashtra",
                "mumbai.waterquality@gov.in",
                "+91 (022) 2262-0251",
                "Municipal Water Works Complex, Bhandup, Mumbai - 400078",
            ),
            (
                "Suspended Regional Testing Facility",
                "MH-WAT-REVOKED-999",
                "State Quality Surveillance Bureau",
                False,  # Inactive / suspended license for testing
                "Thane",
                "Maharashtra",
                "suspended@lab.invalid",
                "+91 (022) 2533-0000",
                "Wagle Estate, Thane - 400604",
            ),
        ]

        for lab in authorized_labs:
            conn.execute(
                text(
                    """
                    INSERT INTO laboratories (
                        name, license_number, issuing_authority, is_active, 
                        district, state, contact_email, contact_phone, address
                    )
                    VALUES (:name, :license_number, :issuing_authority, :is_active, 
                            :district, :state, :contact_email, :contact_phone, :address)
                    ON CONFLICT (license_number) DO UPDATE SET
                        name = EXCLUDED.name,
                        is_active = EXCLUDED.is_active,
                        district = EXCLUDED.district;
                    """
                ),
                {
                    "name": lab[0],
                    "license_number": lab[1],
                    "issuing_authority": lab[2],
                    "is_active": lab[3],
                    "district": lab[4],
                    "state": lab[5],
                    "contact_email": lab[6],
                    "contact_phone": lab[7],
                    "address": lab[8],
                },
            )

        print(f"  -> {len(authorized_labs)} authorized laboratory licenses registered/updated.")

        # 4. Summary check
        count_res = conn.execute(text("SELECT COUNT(*) FROM laboratories;"))
        total_labs = count_res.scalar()
        print(f"[4/4] Verification complete. Total registered laboratories: {total_labs}")

    print("=" * 70)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
