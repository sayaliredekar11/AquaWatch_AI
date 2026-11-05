"""
AquaWatch AI - Authentication & Authorization Router (Lab Authority Policy)

Endpoints:
- POST /auth/register               : Invitation-based registration for authorized Laboratory Authorities
- POST /auth/login                  : OAuth2 form login (strictly restricted to LAB_AUTHORITY; returns signed JWT)
- GET  /auth/invitations/validate   : Validate an invitation token before signup submission
- POST /auth/invitations            : Protected endpoint to generate a new invitation (LAB_AUTHORITY only)
- GET  /auth/me                     : Safe profile information of the current authenticated Lab Authority
- GET  /auth/test/lab               : Protected test route requiring LAB_AUTHORITY role
"""

from datetime import datetime, timezone, timedelta
import hashlib
import os
import secrets
import time
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LabInvitation, Laboratory, LaboratoryLicense, User, UserRole
from app.schemas import (
    LabInvitationCreate,
    LabInvitationResponse,
    LabInvitationValidationResponse,
    LaboratoryResponse,
    LicenseValidationResponse,
    RoleTestResponse,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Authorization"])

# -----------------------------------------------------------------
# Anti-Abuse Rate Limiter for Invalid License Verification Attempts
# -----------------------------------------------------------------
_failed_license_attempts = defaultdict(list)
FAILED_LICENSE_LIMIT = 10
FAILED_WINDOW_SECONDS = 300  # 5 minutes


def _check_license_rate_limit(client_ip: str):
    """Enforces throttling against brute-force laboratory license guessing."""
    now = time.time()
    valid_window = [t for t in _failed_license_attempts[client_ip] if now - t < FAILED_WINDOW_SECONDS]
    _failed_license_attempts[client_ip] = valid_window
    if len(valid_window) >= FAILED_LICENSE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed laboratory license verification attempts. Please wait 5 minutes before trying again.",
        )


def _record_failed_license_attempt(client_ip: str):
    """Logs a failed license attempt for anti-abuse tracking."""
    _failed_license_attempts[client_ip].append(time.time())


# ==========================================================
# 1. License-Verified Lab Authority Registration
# ==========================================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Laboratory Authority account with license verification",
)
def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authorized Laboratory Authority registration with License Number verification:
    - User provides name, email, password, and registered Laboratory License Number.
    - Validates that the license number exists in official registered laboratory records.
    - Ensures the laboratory license is active and authorized.
    - Automatically links the new account to the identified laboratory (no duplicate lab creation).
    - Allows multiple staff members to register under the same valid license.
    - Enforces duplicate email / username uniqueness.
    - Passwords securely hashed with Argon2.
    - Role is permanently and securely assigned as LAB_AUTHORITY on the server.
    - Client can never specify or override the account role.
    """
    client_ip = request.client.host if request.client else "unknown"
    normalized_email = payload.email.strip().lower()

    # 1. Verify email uniqueness (duplicate-email check)
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered. Please log in or use a different email address.",
        )

    # Check optional username uniqueness if provided and distinct
    if payload.username and payload.username.strip():
        norm_username = payload.username.strip().lower()
        if norm_username != normalized_email:
            existing_by_username = db.query(User).filter(User.email == norm_username).first()
            if existing_by_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{payload.username.strip()}' is already in use.",
                )

    # 2. Verify Laboratory License Number (Required & Checked against Database)
    raw_license = payload.license_number or payload.laboratory_license_number
    if not raw_license or not raw_license.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Laboratory License Number is required for Laboratory Authority registration.",
        )

    clean_license = raw_license.strip().upper()

    # Enforce anti-abuse protection against repeated guessing
    _check_license_rate_limit(client_ip)

    # Check whether license exists in registered laboratory records
    license_record = (
        db.query(LaboratoryLicense)
        .filter(func.upper(LaboratoryLicense.license_number) == clean_license)
        .first()
    )

    if not license_record:
        _record_failed_license_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Laboratory License Number '{clean_license}'. The license number is not registered in our authorized laboratory records.",
        )

    # Verify that the license is active and authorized for registration
    if not license_record.is_active:
        _record_failed_license_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Laboratory license '{clean_license}' ({license_record.laboratory_name}) is currently inactive, suspended, or revoked. Please contact the administrator.",
        )

    # 3. Automatic account activation upon verified laboratory license registration
    # No administrator approval required; verified laboratory license authorizes immediate active access.
    is_active = True
    now_utc = datetime.now(timezone.utc)

    # Mark invitation as consumed if present
    pre_auth_invitation = (
        db.query(LabInvitation)
        .filter(
            LabInvitation.email == normalized_email,
            LabInvitation.is_used == False,
        )
        .first()
    )
    if pre_auth_invitation:
        pre_auth_invitation.is_used = True
        pre_auth_invitation.used_at = now_utc

    if payload.invitation_token and payload.invitation_token.strip():
        clean_token = payload.invitation_token.strip()
        token_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()
        token_invitation = (
            db.query(LabInvitation)
            .filter(
                LabInvitation.token_hash == token_hash,
                LabInvitation.is_used == False,
            )
            .first()
        )
        if token_invitation:
            token_invitation.is_used = True
            token_invitation.used_at = now_utc

    # 4. Securely hash password with Argon2
    hashed_pwd = hash_password(payload.password)

    # 5. Create new Lab Authority user linked to the verified laboratory
    new_user = User(
        name=payload.name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        role=UserRole.LAB_AUTHORITY,
        is_active=is_active,
        laboratory_id=license_record.id,
        laboratory_license_number=license_record.license_number,
        laboratory_name=license_record.laboratory_name,
        designation=payload.designation.strip() if payload.designation else "Authorized Laboratory Analyst",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==========================================================
# 2. Validate Laboratory License Number (Pre-flight check)
# ==========================================================
@router.get(
    "/licenses/validate",
    response_model=LicenseValidationResponse,
    summary="Validate a Laboratory License Number before submitting registration",
)
def validate_laboratory_license(
    license_number: str = Query(..., min_length=1, description="Laboratory License Number"),
    db: Session = Depends(get_db),
):
    """
    Checks the existence, authorization, and active status of a Laboratory License Number.
    Safe for frontend validation without leaking internal secrets.
    """
    clean_license = license_number.strip().upper()
    license_record = (
        db.query(LaboratoryLicense)
        .filter(func.upper(LaboratoryLicense.license_number) == clean_license)
        .first()
    )

    if not license_record:
        return {
            "valid": False,
            "license_number": clean_license,
            "laboratory_name": None,
            "district": None,
            "state": None,
            "is_active": False,
            "message": f"License '{clean_license}' is not registered with the water quality regulatory authority.",
        }

    if not license_record.is_active:
        return {
            "valid": False,
            "license_number": license_record.license_number,
            "laboratory_name": license_record.laboratory_name,
            "district": None,
            "state": None,
            "is_active": False,
            "message": f"Laboratory license '{clean_license}' ({license_record.laboratory_name}) is currently inactive or suspended.",
        }

    return {
        "valid": True,
        "license_number": license_record.license_number,
        "laboratory_name": license_record.laboratory_name,
        "district": None,
        "state": "Maharashtra",
        "is_active": True,
        "message": f"Verified: Registered to {license_record.laboratory_name}.",
    }


# ==========================================================
# 2. Validate Invitation Token (Public pre-flight check)
# ==========================================================
@router.get(
    "/invitations/validate",
    response_model=LabInvitationValidationResponse,
    summary="Validate an invitation token before submitting registration",
)
def validate_invitation(
    token: str = Query(..., min_length=1, description="Signup invitation token"),
    db: Session = Depends(get_db),
):
    """
    Checks the validity, email restriction, and expiration of a signup invitation token.
    Safe for frontend validation without leaking internal hashes or credentials.
    """
    clean_token = token.strip()
    token_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()

    invitation = (
        db.query(LabInvitation)
        .filter(LabInvitation.token_hash == token_hash)
        .first()
    )

    if not invitation:
        return {
            "valid": False,
            "email": None,
            "expires_at": None,
            "message": "Invalid invitation token. Please check the code provided.",
        }

    if invitation.is_used:
        return {
            "valid": False,
            "email": invitation.email,
            "expires_at": invitation.expires_at,
            "message": "This invitation token has already been used.",
        }

    now_utc = datetime.now(timezone.utc)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now_utc > expires_at:
        return {
            "valid": False,
            "email": invitation.email,
            "expires_at": invitation.expires_at,
            "message": "This invitation token has expired.",
        }

    return {
        "valid": True,
        "email": invitation.email,
        "expires_at": invitation.expires_at,
        "message": "Invitation token is valid. You may complete registration.",
    }


# ==========================================================
# 3. Create Invitation Token (Protected for LAB_AUTHORITY)
# ==========================================================
@router.post(
    "/invitations",
    response_model=LabInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a signup invitation token for a new Lab Authority (Lab Authority only)",
)
def create_invitation(
    payload: LabInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """
    Generates a cryptographically secure, unpredictable, single-use, expiring invitation token.
    Only authenticated Laboratory Authorities or administrators may issue invitations.
    The raw token is returned once and NEVER stored unhashed in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    now_utc = datetime.now(timezone.utc)
    expires_at = now_utc + timedelta(hours=payload.expires_in_hours)

    target_email = payload.email.strip().lower() if payload.email else None

    # Check if target email is already registered
    if target_email:
        existing = db.query(User).filter(User.email == target_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{target_email}' is already registered.",
            )

    new_invitation = LabInvitation(
        token_hash=token_hash,
        email=target_email,
        invited_by=current_user.email,
        created_at=now_utc,
        expires_at=expires_at,
        is_used=False,
    )

    db.add(new_invitation)
    db.commit()

    return {
        "invitation_token": raw_token,
        "email": target_email,
        "expires_at": expires_at,
        "message": "Invitation created successfully. Deliver the token securely to the recipient.",
    }


# ==========================================================
# 4. Lab Authority Login (OAuth2 Password Request Form)
# ==========================================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT access token (Lab Authority Only)",
)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2-compliant login endpoint:
    - Accepts username (user's email) and password
    - Verifies credentials against Argon2 hash
    - Checks active account status
    - Restricts login exclusively to accounts with the LAB_AUTHORITY role
    - Returns signed JWT bearer access token
    """
    normalized_identifier = form_data.username.strip().lower()

    # Look up user by case-insensitive email first, then fallback to name/username
    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_identifier)
        .first()
    )
    if not user:
        user = (
            db.query(User)
            .filter(func.lower(User.name) == normalized_identifier)
            .first()
        )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account active status (auto-activate if user is registered under an active laboratory license)
    if not user.is_active and user.laboratory_license_number:
        lic = (
            db.query(LaboratoryLicense)
            .filter(func.upper(LaboratoryLicense.license_number) == user.laboratory_license_number.strip().upper())
            .first()
        )
        if lic and lic.is_active:
            user.is_active = True
            db.commit()
            db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended. Please contact system administrator.",
        )

    # Enforce role restriction: Login is strictly reserved for Laboratory Authorities
    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    if user_role_str.upper() != UserRole.LAB_AUTHORITY.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Access restricted: This portal is reserved exclusively for authorized Laboratory Authorities. "
                "Public monitoring features do not require an account. "
                "To request laboratory access, contact the system administrator."
            ),
        )

    # Generate JWT token
    access_token, expires_in = create_access_token(
        data={"sub": user.email, "role": user_role_str}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


# ==========================================================
# 5. Current User Profile
# ==========================================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user's profile details",
)
def get_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the profile information of the currently authenticated user.
    Requires a valid JWT Bearer token.
    """
    return current_user


# ==========================================================
# 6. Role-Based Access Control Test Endpoints
# ==========================================================
@router.get(
    "/test/normal-user",
    response_model=RoleTestResponse,
    summary="Role test endpoint: NORMAL_USER only",
)
def test_normal_user_access(
    current_user: User = Depends(require_roles(UserRole.NORMAL_USER)),
):
    """Protected test endpoint accessible only to accounts with NORMAL_USER role."""
    return {
        "message": "Access granted: You have verified NORMAL_USER privileges.",
        "user_email": current_user.email,
        "role": current_user.role,
    }


@router.get(
    "/test/lab",
    response_model=RoleTestResponse,
    summary="Role test endpoint: LAB_AUTHORITY only",
)
def test_lab_access(
    current_user: User = Depends(require_roles(UserRole.LAB_AUTHORITY)),
):
    """Protected test endpoint accessible only to accounts with LAB_AUTHORITY role."""
    return {
        "message": "Access granted: You have verified LAB_AUTHORITY privileges.",
        "user_email": current_user.email,
        "role": current_user.role,
    }
