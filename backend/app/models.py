"""
AquaWatch AI - SQLAlchemy ORM Models

Day 1: Foundation
Day 2: User Authentication & Authorization Models (User, UserRole)
Day 3: Water Quality Management Models (WaterBody, WaterQualityRecord)

Note: Complaint management features and tables have been permanently excluded.
"""

import enum
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ==========================================================
# 1. User & Role Models (Day 2)
# ==========================================================

class UserRole(str, enum.Enum):
    """
    Two application roles supported across AquaWatch AI:
    - NORMAL_USER: Default role for general registered public accounts.
    - LAB_AUTHORITY: Authorized water quality laboratory analysts and technicians.
    """
    NORMAL_USER = "NORMAL_USER"
    LAB_AUTHORITY = "LAB_AUTHORITY"


class User(Base):
    """
    User entity representing registered accounts in PostgreSQL.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, native_enum=False, length=30),
        nullable=False,
        default=UserRole.NORMAL_USER,
        server_default=UserRole.NORMAL_USER.value,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}', is_active={self.is_active})>"


# ==========================================================
# 2. Water Body Model (Day 3)
# ==========================================================

class WaterBody(Base):
    """
    Represents a monitored body of water (e.g. river, lake, reservoir, stream, canal).
    """
    __tablename__ = "water_bodies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    water_body_type = Column(String(50), nullable=False)  # e.g., 'river', 'lake', 'reservoir'
    location_name = Column(String(200), nullable=False)   # e.g., 'Ganga River Basin - Haridwar'
    latitude = Column(Float, nullable=True)               # -90.0 to 90.0
    longitude = Column(Float, nullable=True)              # -180.0 to 180.0
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Database-level integrity constraints
    __table_args__ = (
        CheckConstraint("latitude >= -90.0 AND latitude <= 90.0", name="check_latitude_range"),
        CheckConstraint("longitude >= -180.0 AND longitude <= 180.0", name="check_longitude_range"),
    )

    # Linked measurement records - intentionally do NOT use cascade delete-orphan
    # Linked measurements must not be silently lost when a water body is targeted for deletion.
    records = relationship("WaterQualityRecord", back_populates="water_body")

    def __repr__(self):
        return f"<WaterBody(id={self.id}, name='{self.name}', type='{self.water_body_type}')>"


# ==========================================================
# 3. Water Quality Measurement Record Model (Day 3)
# ==========================================================

class WaterQualityRecord(Base):
    """
    Stores individual laboratory or sensor water quality parameter measurements.
    
    Documented Parameter Units:
    - ph: Dimensionless pH scale (0.0 - 14.0)
    - dissolved_oxygen: mg/L (Milligrams per liter)
    - bod: mg/L (Biochemical Oxygen Demand)
    - turbidity: NTU (Nephelometric Turbidity Units)
    - tds: mg/L (Total Dissolved Solids)
    - electrical_conductivity: µS/cm (MicroSiemens per centimeter)
    - nitrate: mg/L (Milligrams per liter)
    - temperature: °C (Degrees Celsius)
    """
    __tablename__ = "water_quality_records"

    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(
        Integer,
        ForeignKey("water_bodies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ph = Column(Float, nullable=True)
    dissolved_oxygen = Column(Float, nullable=True)
    bod = Column(Float, nullable=True)
    turbidity = Column(Float, nullable=True)
    tds = Column(Float, nullable=True)
    electrical_conductivity = Column(Float, nullable=True)
    nitrate = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Database-level integrity constraints for valid parameter bounds
    __table_args__ = (
        CheckConstraint("ph >= 0.0 AND ph <= 14.0", name="check_ph_range"),
        CheckConstraint("dissolved_oxygen >= 0.0", name="check_do_non_negative"),
        CheckConstraint("bod >= 0.0", name="check_bod_non_negative"),
        CheckConstraint("turbidity >= 0.0", name="check_turbidity_non_negative"),
        CheckConstraint("tds >= 0.0", name="check_tds_non_negative"),
        CheckConstraint("electrical_conductivity >= 0.0", name="check_ec_non_negative"),
        CheckConstraint("nitrate >= 0.0", name="check_nitrate_non_negative"),
    )

    # Relationship back to the monitored water body
    water_body = relationship("WaterBody", back_populates="records")

    def __repr__(self):
        return f"<WaterQualityRecord(id={self.id}, water_body_id={self.water_body_id}, measured_at='{self.measured_at}')>"


# ==========================================================
# 4. Lab Authority Signup Invitation Model
# ==========================================================

class LabInvitation(Base):
    """
    Stores cryptographically secure signup invitations for Laboratory Authorities.
    Raw invitation tokens are NEVER stored in the database; only their SHA-256 hashes are persisted.
    """
    __tablename__ = "lab_invitations"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True, index=True)  # Optional specific email restriction
    invited_by = Column(String(255), nullable=True)         # Admin email or 'CLI'
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False, server_default="false")
    used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<LabInvitation(id={self.id}, email='{self.email}', is_used={self.is_used})>"

