"""
AquaWatch AI - Safe Administrative Procedure for LAB_AUTHORITY Assignment

Command-line administrative utility to safely assign or manage LAB_AUTHORITY accounts.
Operates directly through local server terminal and database credentials.
Does NOT expose any unauthenticated or remote HTTP promotion endpoints.
Does NOT require a third application role.

Supported commands:
  --list                            : List all registered accounts and roles
  --create                          : Directly provision a new LAB_AUTHORITY account
  --invite                          : Generate a cryptographically secure, single-use signup invitation
  --promote <email>                 : Promote an existing account to LAB_AUTHORITY
  --demote <email>                  : Demote a LAB_AUTHORITY account to NORMAL_USER
"""

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import sys
from typing import Optional
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import LabInvitation, User, UserRole
from app.security import hash_password


def list_users(db: Session):
    """List all registered users and their current role."""
    users = db.query(User).order_by(User.id).all()
    print("=" * 65)
    print(f"{'ID':<6} {'Name':<20} {'Email':<25} {'Role':<15}")
    print("=" * 65)
    for u in users:
        print(f"{u.id:<6} {u.name[:18]:<20} {u.email[:23]:<25} {u.role.value:<15}")
    print("=" * 65)


def promote_user(db: Session, email: str):
    """Promote an existing account to LAB_AUTHORITY."""
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        print(f"[ERROR] User with email '{normalized_email}' not found.")
        sys.exit(1)

    if user.role == UserRole.LAB_AUTHORITY:
        print(f"[INFO] User '{normalized_email}' is already assigned 'LAB_AUTHORITY'.")
        return

    user.role = UserRole.LAB_AUTHORITY
    db.commit()
    db.refresh(user)
    print(f"[SUCCESS] User '{user.email}' (ID #{user.id}) successfully assigned role 'LAB_AUTHORITY'.")


def demote_user(db: Session, email: str):
    """Demote a LAB_AUTHORITY to NORMAL_USER."""
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        print(f"[ERROR] User with email '{normalized_email}' not found.")
        sys.exit(1)

    user.role = UserRole.NORMAL_USER
    db.commit()
    db.refresh(user)
    print(f"[SUCCESS] User '{user.email}' (ID #{user.id}) role changed to 'NORMAL_USER'.")


def create_lab_user(db: Session, name: str, email: str, password: str):
    """Directly create and provision a new LAB_AUTHORITY account."""
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        print(f"[ERROR] An account with email '{normalized_email}' already exists (Current Role: {existing.role.value}).")
        print("Use --promote to upgrade this account.")
        sys.exit(1)

    if len(password) < 6:
        print("[ERROR] Password must be at least 6 characters long.")
        sys.exit(1)

    hashed_pwd = hash_password(password)
    new_lab_user = User(
        name=name.strip(),
        email=normalized_email,
        hashed_password=hashed_pwd,
        role=UserRole.LAB_AUTHORITY,
        is_active=True,
    )

    db.add(new_lab_user)
    db.commit()
    db.refresh(new_lab_user)
    print(f"[SUCCESS] Laboratory authority created: '{new_lab_user.email}' (ID #{new_lab_user.id}) with role 'LAB_AUTHORITY'.")


def create_invitation(db: Session, email: Optional[str] = None, hours: int = 48):
    """
    Generate and store an invitation token hash, returning the raw token.
    The raw token is single-use and expiring, and is never stored unhashed in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now_utc = datetime.now(timezone.utc)
    expires_at = now_utc + timedelta(hours=hours)

    target_email = email.strip().lower() if email else None
    if target_email:
        existing = db.query(User).filter(User.email == target_email).first()
        if existing:
            print(f"[ERROR] An account with email '{target_email}' already exists.")
            sys.exit(1)

    invitation = LabInvitation(
        token_hash=token_hash,
        email=target_email,
        invited_by="CLI",
        created_at=now_utc,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(invitation)
    db.commit()

    print("=" * 65)
    print("AQUAWATCH AI — LAB AUTHORITY INVITATION GENERATED")
    print("=" * 65)
    print(f"Invitation Token : {raw_token}")
    if target_email:
        print(f"Restricted To    : {target_email}")
    else:
        print(f"Restricted To    : (Any authorized applicant)")
    print(f"Expires At (UTC) : {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')} ({hours} hours)")
    print("=" * 65)
    print("Direct Registration URL for the applicant:")
    print(f"http://localhost:5173/signup?token={raw_token}")
    print("=" * 65)


def list_invitations(db: Session):
    """List recent invitations and their status."""
    invitations = db.query(LabInvitation).order_by(LabInvitation.created_at.desc()).limit(20).all()
    print("=" * 75)
    print(f"{'ID':<6} {'Target Email':<25} {'Expires At (UTC)':<22} {'Status':<12}")
    print("=" * 75)
    now_utc = datetime.now(timezone.utc)
    for inv in invitations:
        exp = inv.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if inv.is_used:
            status_str = "USED"
        elif now_utc > exp:
            status_str = "EXPIRED"
        else:
            status_str = "ACTIVE"
        email_str = inv.email[:23] if inv.email else "(any)"
        exp_str = exp.strftime("%Y-%m-%d %H:%M")
        print(f"{inv.id:<6} {email_str:<25} {exp_str:<22} {status_str:<12}")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description="AquaWatch AI - Safe Administrative Management for LAB_AUTHORITY Accounts"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list",
        action="store_true",
        help="List all users and their assigned roles",
    )
    group.add_argument(
        "--promote",
        metavar="EMAIL",
        help="Promote an existing registered user to LAB_AUTHORITY",
    )
    group.add_argument(
        "--demote",
        metavar="EMAIL",
        help="Demote an existing LAB_AUTHORITY user to NORMAL_USER",
    )
    group.add_argument(
        "--create",
        action="store_true",
        help="Create a new LAB_AUTHORITY account (requires --name, --email, --password)",
    )
    group.add_argument(
        "--invite",
        action="store_true",
        help="Generate a signup invitation token for a new Lab Authority (optional --email, --hours)",
    )
    group.add_argument(
        "--list-invites",
        action="store_true",
        help="List recent invitations and their active/used/expired status",
    )

    parser.add_argument("--name", help="User full name (for --create)")
    parser.add_argument("--email", help="User email address (for --create, --promote, or --invite)")
    parser.add_argument("--password", help="User password (for --create)")
    parser.add_argument("--hours", type=int, default=48, help="Invitation validity in hours (default 48)")

    args = parser.parse_args()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        if args.list:
            list_users(db)
        elif args.promote:
            promote_user(db, args.promote)
        elif args.demote:
            demote_user(db, args.demote)
        elif args.create:
            if not args.name or not args.email or not args.password:
                print("[ERROR] --create requires --name, --email, and --password.")
                sys.exit(1)
            create_lab_user(db, args.name, args.email, args.password)
        elif args.invite:
            create_invitation(db, email=args.email, hours=args.hours)
        elif args.list_invites:
            list_invitations(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
