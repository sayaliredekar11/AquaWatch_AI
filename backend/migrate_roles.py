"""
AquaWatch AI - Role Migration Script
Migrates database users from the legacy 4-role schema to the simplified 2-role schema:
- 'CITIZEN' -> 'NORMAL_USER'
- 'LAB_AUTHORITY' remains 'LAB_AUTHORITY'
- Reports any unresolved roles (such as legacy 'POLLUTION_OFFICIAL' or 'ADMIN') without destructive modification.
"""

from sqlalchemy import text
from app.database import engine

def run_migration():
    print("=" * 60)
    print("AQUAWATCH AI: ROLE MIGRATION TO TWO-ROLE SCHEMA")
    print("=" * 60)

    with engine.begin() as conn:
        # 1. Inspect existing users
        rows = conn.execute(text("SELECT id, name, email, role FROM users ORDER BY id")).fetchall()
        print(f"Total existing users in database: {len(rows)}")
        for r in rows:
            print(f" - User #{r.id}: {r.email} (Current Role: {r.role})")

        # 2. Check for CITIZEN accounts to migrate
        citizen_count = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE role = 'CITIZEN'")
        ).scalar()

        if citizen_count > 0:
            print(f"\nMigrating {citizen_count} 'CITIZEN' account(s) to 'NORMAL_USER'...")
            conn.execute(text("UPDATE users SET role = 'NORMAL_USER' WHERE role = 'CITIZEN'"))
            print("Successfully updated 'CITIZEN' -> 'NORMAL_USER'.")
        else:
            print("\nNo 'CITIZEN' accounts found requiring migration.")

        # 3. Check for any unresolved roles
        unresolved = conn.execute(
            text("SELECT id, email, role FROM users WHERE role NOT IN ('NORMAL_USER', 'LAB_AUTHORITY')")
        ).fetchall()

        if unresolved:
            print("\n[WARNING] Unresolved role accounts detected:")
            for u in unresolved:
                print(f" - ID {u.id}: {u.email} has legacy role '{u.role}'")
        else:
            print("\nAll database accounts now strictly use 'NORMAL_USER' or 'LAB_AUTHORITY'.")

        # 4. Verify post-migration state
        updated_rows = conn.execute(text("SELECT id, name, email, role FROM users ORDER BY id")).fetchall()
        print("\nPost-Migration User Summary:")
        for r in updated_rows:
            print(f" - User #{r.id}: {r.email} -> Role: {r.role}")

    print("=" * 60)
    print("ROLE MIGRATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_migration()
