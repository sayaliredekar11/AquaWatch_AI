"""
AquaWatch AI - Database Migration: Add ML Features to WaterQualityRecord
Adds cod, ammonia_n, chlorides, sulphate, fecal_coliform, total_coliform as nullable columns.
Does NOT modify or delete any existing records.
"""

from app.database import engine
from sqlalchemy import text

def run_migration():
    print("Running database migration: Adding 12-feature ML columns to water_quality_records...")
    columns = [
        ("cod", "FLOAT"),
        ("ammonia_n", "FLOAT"),
        ("chlorides", "FLOAT"),
        ("sulphate", "FLOAT"),
        ("fecal_coliform", "FLOAT"),
        ("total_coliform", "FLOAT"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in columns:
            sql = f"ALTER TABLE water_quality_records ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            conn.execute(text(sql))
            print(f"  [OK] Column '{col_name}' ({col_type}) verified.")
        conn.commit()
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
