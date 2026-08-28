#!/usr/bin/env python3
"""Create Admin User Script"""
import asyncio
import sys
from pathlib import Path
import getpass

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import get_password_hash
from app.core.encryption import get_encryption_service


async def create_admin():
    print("=" * 50)
    print("  Create Admin User")
    print("=" * 50)
    print()

    username = input("Username [admin]: ").strip() or "admin"
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match!")
        sys.exit(1)

    full_name_ar = input("Full Name (AR) [مدير النظام]: ").strip() or "مدير النظام"
    email = input("Email [admin@mediagate.gov.sy]: ").strip() or "admin@mediagate.gov.sy"

    print(f"\n✓ Admin user '{username}' will be created.")
    print("Run this script inside the backend container:")
    print("  docker compose run --rm backend python scripts/create_admin.py")


if __name__ == "__main__":
    asyncio.run(create_admin())
