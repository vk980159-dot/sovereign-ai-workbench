"""
Sovereign AI Workbench - Administrative Bootstrap Utility (SIH26117)
Enables offline administrators to provision or reset the initial administrator account.
Runs 100% locally with Argon2id password hashing and SHA-256 ledger auditing.

Usage:
    python bootstrap_admin.py --username admin --email admin@sovereign.local --name "Sovereign Administrator"
    (Will prompt securely for password if not passed via --password)
"""

import sys
import os
import argparse
import getpass

# Ensure app package is accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.security.auth import (
    init_auth_db,
    bootstrap_admin_user,
    validate_password_strength
)


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap or reset the primary administrator account for Sovereign AI Workbench."
    )
    parser.add_argument(
        "--username", "-u",
        default=settings.ADMIN_DEFAULT_USERNAME,
        help="Administrator username (default: admin)"
    )
    parser.add_argument(
        "--email", "-e",
        default=getattr(settings, "ADMIN_DEFAULT_EMAIL", "admin@sovereign.local"),
        help="Administrator email (default: admin@sovereign.local)"
    )
    parser.add_argument(
        "--name", "-n",
        default=getattr(settings, "ADMIN_DEFAULT_FULL_NAME", "Sovereign Administrator"),
        help="Administrator full name (default: Sovereign Administrator)"
    )
    parser.add_argument(
        "--password", "-p",
        help="Administrator password (if omitted, you will be prompted securely)"
    )

    args = parser.parse_args()

    print("=" * 65)
    print(" [SOVEREIGN AI WORKBENCH - LOCAL ADMIN PROVISIONING]")
    print("=" * 65)

    password = args.password
    if not password:
        password = getpass.getpass(" Enter administrator password: ")
        confirm = getpass.getpass(" Confirm administrator password: ")
        if password != confirm:
            print("\n [ERROR]: Passwords do not match.")
            sys.exit(1)

    is_strong, reason = validate_password_strength(password)
    if not is_strong:
        print(f"\n [ERROR]: {reason}")
        sys.exit(1)

    # Initialize auth database schema if needed
    init_auth_db()

    # Provision admin
    success = bootstrap_admin_user(
        username=args.username,
        password=password,
        email=args.email,
        full_name=args.name
    )

    if success:
        print("\n [SUCCESS]: Sovereign Administrator account provisioned successfully.")
        print(f"            Username:  {args.username}")
        print(f"            Email:     {args.email}")
        print(f"            Full Name: {args.name}")
        print("            Role:      admin")
        print("            Storage:   Local SQLite (auth.db) with Argon2id hashing")
        print("            Audit:     Cryptographically sealed in SHA-256 micro-ledger")
        print("=" * 65)
    else:
        print("\n [ERROR]: Failed to provision administrator account.")
        sys.exit(1)


if __name__ == "__main__":
    main()
