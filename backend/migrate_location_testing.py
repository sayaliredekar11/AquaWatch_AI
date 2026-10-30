"""
AquaWatch AI - Database Migration: Location-Based Water Testing
Adds district and state to water_bodies.
Adds sample_name, wqi_score, wqi_prediction, wqi_status, wqi_algorithm, safety_classification to water_quality_records.
Preserves all existing data and database integrity.
"""

import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from sqlalchemy import text
from app.database import engine

def run_migration():
    print("Running migration for Location-Based Water Testing...")
    wb_cols = [
        ("district", "VARCHAR(100)"),
        ("state", "VARCHAR(100) DEFAULT 'Maharashtra'"),
    ]
    wqr_cols = [
        ("sample_name", "VARCHAR(100)"),
        ("wqi_score", "FLOAT"),
        ("wqi_prediction", "VARCHAR(50)"),
        ("wqi_status", "VARCHAR(50)"),
        ("wqi_algorithm", "VARCHAR(100)"),
        ("safety_classification", "VARCHAR(50)"),
    ]

    with engine.connect() as conn:
        for col_name, col_type in wb_cols:
            sql = f"ALTER TABLE water_bodies ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            conn.execute(text(sql))
            print(f"  [OK] water_bodies.{col_name} checked/added.")

        for col_name, col_type in wqr_cols:
            sql = f"ALTER TABLE water_quality_records ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            conn.execute(text(sql))
            print(f"  [OK] water_quality_records.{col_name} checked/added.")

        # Update existing water bodies with districts if null
        conn.execute(text("""
            UPDATE water_bodies
            SET state = 'Maharashtra'
            WHERE state IS NULL;
        """))
        conn.execute(text("""
            UPDATE water_bodies
            SET district = 'Sangli'
            WHERE (district IS NULL OR district = '') AND (name ILIKE '%Sangli%' OR location_name ILIKE '%Sangli%');
        """))
        conn.execute(text("""
            UPDATE water_bodies
            SET district = 'Kolhapur'
            WHERE (district IS NULL OR district = '') AND (name ILIKE '%Kolhapur%' OR location_name ILIKE '%Kolhapur%');
        """))
        conn.execute(text("""
            UPDATE water_bodies
            SET district = 'Pune'
            WHERE (district IS NULL OR district = '') AND (name ILIKE '%Pune%' OR location_name ILIKE '%Pune%');
        """))
        conn.execute(text("""
            UPDATE water_bodies
            SET district = 'Varanasi', state = 'Uttar Pradesh'
            WHERE (district IS NULL OR district = '') AND (name ILIKE '%Varanasi%' OR location_name ILIKE '%Varanasi%' OR name ILIKE '%Ganges%');
        """))

        conn.commit()
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
