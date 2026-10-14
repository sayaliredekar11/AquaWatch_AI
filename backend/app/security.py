"""
AquaWatch AI - Security & Authentication Utilities

Handles:
- Secure password hashing and verification with Argon2
- JWT access token generation, encoding, and decoding
- OAuth2 Bearer token extraction and authentication dependency
- Role-based authorization enforcement (RBAC)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole

# 1. Load environment variables
load_dotenv()

# 2. Secret configurations from .env
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "replace-with-a-secure-secret-key-at-least-32-chars-long",
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 3. Secure password hashing with Argon2
password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against an Argon2 hash."""
    return password_hasher.verify(plain_password, hashed_password)


# 4. OAuth2 password bearer scheme for extracting tokens from Authorization headers
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    description="Enter your access token received from /auth/login",
)


# 5. JWT Access Token Creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
    """
    Generate a signed JWT access token.
    Returns:
        tuple[str, int]: (encoded_jwt_token, expiration_duration_seconds)
    """
    to_encode = data.copy()
    if expires_delta:
        expire_time = datetime.now(timezone.utc) + expires_delta
        expires_seconds = int(expires_delta.total_seconds())
    else:
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60

    to_encode.update({"exp": expire_time})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expires_seconds


# 6. Current User Authentication Dependency
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to authenticate requests using JWT Bearer token.
    Decodes token, extracts user email, verifies active status, and loads user from database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    # Query current user state from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Access forbidden.",
        )

    return user


# 7. Role-Based Access Control (RBAC) Dependency
class RoleChecker:
    """
    Dependency callable that verifies whether the authenticated user has one of the allowed roles.
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Insufficient permissions. Required role: {[r.value for r in self.allowed_roles]}.",
            )
        return current_user


def require_roles(*roles: UserRole):
    """
    Helper function to instantiate RoleChecker.
    Example:
        @router.get("/admin-only")
        def admin_view(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    return RoleChecker(list(roles))
