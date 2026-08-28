#!/usr/bin/env python3
"""Create Admin User Script — actually writes the user, non-destructively.

Unlike seed_demo.py, this never touches existing data: it only inserts one
new user (after checking the username isn't already taken).
"""
import asyncio
import sys
from pathlib import Path
import getpass

sys.path.insert(0, str(Path(__file__).parent.parent))

import pyotp
from sqlalchemy import select

from app.db.session import async_session_maker
from app.models import User, Department
from app.core.security import get_password_hash, validate_password_strength, generate_totp_secret
from app.core.encryption import get_encryption_service


async def create_admin():
    print("=" * 50)
    print("  Create Admin User")
    print("=" * 50)
    print()

    username = input("Username [admin]: ").strip() or "admin"

    while True:
        password = getpass.getpass("Password (min. 10 chars, mixed case/digits/symbols): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match, try again.\n")
            continue
        try:
            validate_password_strength(password)
            break
        except ValueError as e:
            print(f"{e}\n")

    full_name_ar = input("Full Name (AR) [مدير النظام]: ").strip() or "مدير النظام"
    full_name_en = input("Full Name (EN) [System Administrator]: ").strip() or "System Administrator"
    email = input("Email [admin@mediagate.gov.sy]: ").strip() or "admin@mediagate.gov.sy"

    enc = get_encryption_service()

    async with async_session_maker() as session:
        existing = await session.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            print(f"\n✗ Username '{username}' already exists. Nothing was changed.")
            return

        dept_result = await session.execute(select(Department.id).limit(1))
        dept_row = dept_result.fetchone()
        department_id = dept_row[0] if dept_row else None

        totp_secret = pyotp.random_base32()
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            full_name_ar=full_name_ar,
            full_name_en=full_name_en,
            email=enc.encrypt(email, context="email"),
            phone=enc.encrypt("", context="phone"),
            role="super_admin",
            department_id=department_id,
            totp_secret=enc.encrypt(totp_secret, context="totp_secret"),
            is_active=True,
        )
        session.add(user)
        await session.commit()

    print(f"\n✓ Admin user '{username}' created.")
    print(f"  TOTP secret (scan into an authenticator app now, it is never shown again): {totp_secret}")
    print(f"  Current code: {pyotp.TOTP(totp_secret).now()}")


if __name__ == "__main__":
    asyncio.run(create_admin())
