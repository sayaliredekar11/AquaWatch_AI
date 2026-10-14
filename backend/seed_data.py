"""
AquaWatch AI - Demonstration Database Seed Script
Populates PostgreSQL with:
- 1 Normal User (user@aquawatch.ai / user123)
- 1 Lab Authority (lab@aquawatch.ai / lab123)
- Real monitored water bodies with coordinates
- Real water quality sampling measurements
"""

from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app.models import User, UserRole, WaterBody, WaterQualityRecord
from app.security import hash_password

def seed_database():
    db = SessionLocal()
    try:
        print("Seeding AquaWatch demonstration data...")

        # 1. Seed Normal User
        norm_email = "user@aquawatch.ai"
        user_norm = db.query(User).filter(User.email == norm_email).first()
        if not user_norm:
            user_norm = User(
                name="Aarav Sharma (Citizen)",
                email=norm_email,
                hashed_password=hash_password("user123"),
                role=UserRole.NORMAL_USER,
                is_active=True,
            )
            db.add(user_norm)
            print(f"Created Normal User: {norm_email}")

        # 2. Seed Lab Authority
        lab_email = "lab@aquawatch.ai"
        user_lab = db.query(User).filter(User.email == lab_email).first()
        if not user_lab:
            user_lab = User(
                name="Dr. Sunita Patil (Lab Authority)",
                email=lab_email,
                hashed_password=hash_password("lab123"),
                role=UserRole.LAB_AUTHORITY,
                is_active=True,
            )
            db.add(user_lab)
            print(f"Created Lab Authority User: {lab_email}")
        else:
            user_lab.role = UserRole.LAB_AUTHORITY

        db.commit()

        # 3. Seed Water Bodies
        stations = [
            {
                "name": "Krishna River — Sangli Ghat",
                "water_body_type": "river",
                "location_name": "Sangli Pier, Maharashtra",
                "latitude": 16.8524,
                "longitude": 74.5815,
            },
            {
                "name": "Panchganga River — Kolhapur",
                "water_body_type": "river",
                "location_name": "Shiroli Bridge, Kolhapur",
                "latitude": 16.7050,
                "longitude": 74.2433,
            },
            {
                "name": "Mula-Mutha River — Pune",
                "water_body_type": "river",
                "location_name": "Bund Garden, Pune",
                "latitude": 18.5204,
                "longitude": 73.8567,
            },
            {
                "name": "Ganges River — Assi Ghat",
                "water_body_type": "river",
                "location_name": "Varanasi, Uttar Pradesh",
                "latitude": 25.2974,
                "longitude": 83.0064,
            },
        ]

        created_bodies = []
        for s in stations:
            wb = db.query(WaterBody).filter(WaterBody.name == s["name"]).first()
            if not wb:
                wb = WaterBody(**s)
                db.add(wb)
                db.commit()
                db.refresh(wb)
                print(f"Created Water Body: {wb.name} (ID: {wb.id})")
            created_bodies.append(wb)

        # 4. Seed Measurement Records
        now = datetime.now(timezone.utc)
        measurements_data = [
            # Krishna River measurements
            {
                "water_body_id": created_bodies[0].id,
                "ph": 7.4,
                "dissolved_oxygen": 6.8,
                "bod": 2.2,
                "turbidity": 4.1,
                "tds": 240.0,
                "electrical_conductivity": 350.0,
                "nitrate": 1.2,
                "temperature": 24.5,
                "measured_at": now - timedelta(days=1),
            },
            {
                "water_body_id": created_bodies[0].id,
                "ph": 7.2,
                "dissolved_oxygen": 6.5,
                "bod": 2.5,
                "turbidity": 4.8,
                "tds": 255.0,
                "electrical_conductivity": 360.0,
                "nitrate": 1.4,
                "temperature": 25.0,
                "measured_at": now - timedelta(days=5),
            },
            {
                "water_body_id": created_bodies[0].id,
                "ph": 7.6,
                "dissolved_oxygen": 7.0,
                "bod": 1.9,
                "turbidity": 3.8,
                "tds": 230.0,
                "electrical_conductivity": 340.0,
                "nitrate": 1.1,
                "temperature": 23.5,
                "measured_at": now - timedelta(days=12),
            },
            # Panchganga River
            {
                "water_body_id": created_bodies[1].id,
                "ph": 6.9,
                "dissolved_oxygen": 5.4,
                "bod": 4.2,
                "turbidity": 8.5,
                "tds": 380.0,
                "electrical_conductivity": 420.0,
                "nitrate": 2.8,
                "temperature": 26.0,
                "measured_at": now - timedelta(days=2),
            },
            # Mula-Mutha River
            {
                "water_body_id": created_bodies[2].id,
                "ph": 6.6,
                "dissolved_oxygen": 4.1,
                "bod": 6.5,
                "turbidity": 12.0,
                "tds": 490.0,
                "electrical_conductivity": 510.0,
                "nitrate": 4.2,
                "temperature": 27.2,
                "measured_at": now - timedelta(days=3),
            },
            # Ganges River
            {
                "water_body_id": created_bodies[3].id,
                "ph": 7.8,
                "dissolved_oxygen": 7.2,
                "bod": 2.8,
                "turbidity": 6.0,
                "tds": 280.0,
                "electrical_conductivity": 390.0,
                "nitrate": 1.6,
                "temperature": 22.0,
                "measured_at": now - timedelta(hours=8),
            },
        ]

        existing_count = db.query(WaterQualityRecord).count()
        if existing_count == 0:
            for m in measurements_data:
                db.add(WaterQualityRecord(**m))
            db.commit()
            print(f"Added {len(measurements_data)} realistic water quality records.")
        else:
            print(f"Database already contains {existing_count} measurement records.")

        print("Seeding complete successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
