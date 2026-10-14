"""
AquaWatch AI - Safe Administrative Procedure for LAB_AUTHORITY Assignment

Command-line administrative utility to safely assign or manage LAB_AUTHORITY accounts.
Operates directly through local server terminal and database credentials.
Does NOT expose any unauthenticated or remote HTTP promotion endpoints.
Does NOT require a third application role.
"""

import argparse
import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, UserRole
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
    """Promote an existing NORMAL_USER to LAB_AUTHORITY."""
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

    parser.add_argument("--name", help="User full name (for --create)")
    parser.add_argument("--email", help="User email address (for --create)")
    parser.add_argument("--password", help="User password (for --create)")

    args = parser.parse_args()

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
    finally:
        db.close()


if __name__ == "__main__":
    main()
