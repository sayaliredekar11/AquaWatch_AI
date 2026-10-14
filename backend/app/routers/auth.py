"""
AquaWatch AI - Authentication & Authorization Router

Endpoints:
- POST /auth/register       : User registration (assigns CITIZEN role by default)
- POST /auth/login          : OAuth2 compatible form login (returns signed JWT)
- GET  /auth/me             : Safe profile information of the current authenticated user
- GET  /auth/test/citizen   : Protected route requiring CITIZEN role
- GET  /auth/test/lab       : Protected route requiring LAB_AUTHORITY role
- GET  /auth/test/official  : Protected route requiring POLLUTION_OFFICIAL role
- GET  /auth/test/admin     : Protected route requiring ADMIN role
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import (
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
# 1. User Registration
# ==========================================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user account:
    - Validates email and password length
    - Checks for duplicate emails
    - Hashes password using Argon2
    - Enforces default 'CITIZEN' role (public registration cannot claim privileged roles)
    """
    normalized_email = payload.email.strip().lower()

    # Verify email uniqueness
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered. Please log in or use a different email address.",
        )

    # Securely hash password
    hashed_pwd = hash_password(payload.password)

    # Create new normal user
    new_user = User(
        name=payload.name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        role=UserRole.NORMAL_USER,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==========================================================
# 2. User Login (OAuth2 Password Request Form)
# ==========================================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT access token",
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
            detail="Account is inactive. Please contact system administrator.",
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
# 3. Current User Profile
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
# 4. Role-Based Access Control Test Endpoints
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
