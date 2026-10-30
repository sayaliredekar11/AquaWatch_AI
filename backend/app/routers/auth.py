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
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LabInvitation, User, UserRole
from app.schemas import (
    LabInvitationCreate,
    LabInvitationResponse,
    LabInvitationValidationResponse,
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


# ==========================================================
# 1. Invitation-Based Lab Authority Registration
# ==========================================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Laboratory Authority account",
)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Authorized Laboratory Authority registration:
    - User provides name, email, and password. No invitation token is required.
    - Strong server-side validation, duplicate email check, and Argon2 password hashing.
    - Role is permanently and securely assigned as LAB_AUTHORITY on the server.
    - Client can never specify or override the account role.
    - Restricted policy: Unless pre-authorized or REQUIRE_ADMIN_APPROVAL is set to false,
      new accounts are created with is_active=False pending administrator approval.
    """
    normalized_email = payload.email.strip().lower()

    # 1. Verify email uniqueness (duplicate-email check)
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered. Please log in or use a different email address.",
        )

    # 2. Check authorization & administrator approval policy
    require_approval = os.getenv("REQUIRE_ADMIN_APPROVAL", "true").lower() in ("true", "1", "yes")
    now_utc = datetime.now(timezone.utc)
    is_active = False

    # Check if this email was pre-authorized by an administrator in lab_invitations
    pre_auth_invitation = (
        db.query(LabInvitation)
        .filter(
            LabInvitation.email == normalized_email,
            LabInvitation.is_used == False,
        )
        .first()
    )

    # Check optional legacy invitation token if provided
    token_invitation = None
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

    active_invitation = pre_auth_invitation or token_invitation
    if active_invitation:
        exp = active_invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now_utc <= exp:
            is_active = True
            active_invitation.is_used = True
            active_invitation.used_at = now_utc
    elif not require_approval:
        is_active = True
    else:
        is_active = False

    # 3. Securely hash password with Argon2
    hashed_pwd = hash_password(payload.password)

    # 4. Create new Lab Authority user (server-assigned role; client cannot override)
    new_user = User(
        name=payload.name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        role=UserRole.LAB_AUTHORITY,
        is_active=is_active,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


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
    normalized_email = form_data.username.strip().lower()

    # Look up user by email
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending administrator approval. Please contact system administrator.",
        )

    # Enforce role restriction: Login is strictly reserved for Laboratory Authorities
    if user.role != UserRole.LAB_AUTHORITY:
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
        data={"sub": user.email, "role": user.role.value}
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
