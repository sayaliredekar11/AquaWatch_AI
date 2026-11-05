"""
AquaWatch AI - Database Migration: Enhanced Water Testing & PDF Reporting
Adds missing parameters and laboratory/report metadata to water_quality_records:
- phosphate (FLOAT)
- sample_id (VARCHAR(100))
- sample_type (VARCHAR(100))
- laboratory_name (VARCHAR(200))
- lab_authority_name (VARCHAR(100))
- testing_date (TIMESTAMP WITH TIME ZONE)
- testing_method (VARCHAR(150))
- remarks (TEXT)
- report_id (VARCHAR(100))
- pdf_path (VARCHAR(300))
- wqi_category (VARCHAR(100))

Preserves all existing records and relationships.
"""

import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from sqlalchemy import text
from app.database import engine

def run_migration():
    print("Running migration for Enhanced Water Testing & PDF Reporting...")
    
    new_columns = [
        ("phosphate", "FLOAT"),
        ("sample_id", "VARCHAR(100)"),
        ("sample_type", "VARCHAR(100) DEFAULT 'Surface Water'"),
        ("laboratory_name", "VARCHAR(200)"),
        ("lab_authority_name", "VARCHAR(100)"),
        ("testing_date", "TIMESTAMP WITH TIME ZONE"),
        ("testing_method", "VARCHAR(150)"),
        ("remarks", "TEXT"),
        ("report_id", "VARCHAR(100)"),
        ("pdf_path", "VARCHAR(300)"),
        ("wqi_category", "VARCHAR(100)"),
    ]

    with engine.connect() as conn:
        for col_name, col_type in new_columns:
            sql = f"ALTER TABLE water_quality_records ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            conn.execute(text(sql))
            print(f"  [OK] water_quality_records.{col_name} checked/added.")

        # Create indexes for sample_id and report_id if they don't exist
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_water_quality_records_sample_id 
            ON water_quality_records (sample_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_water_quality_records_report_id 
            ON water_quality_records (report_id);
        """))

        # Backfill existing records with sample_id and report_id if null
        conn.execute(text("""
            UPDATE water_quality_records
            SET sample_id = 'SMP-LEGACY-' || id
            WHERE sample_id IS NULL;
        """))
        conn.execute(text("""
            UPDATE water_quality_records
            SET report_id = 'REP-LEGACY-' || id
            WHERE report_id IS NULL;
        """))
        conn.execute(text("""
            UPDATE water_quality_records
            SET sample_type = 'Surface Water'
            WHERE sample_type IS NULL;
        """))

        conn.commit()
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
