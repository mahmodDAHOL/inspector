#!/usr/bin/env python3
"""Reset TOTP Secret Script — the official, repeatable way to get a fresh
Base32 TOTP secret for an *existing* account.

The app deliberately never exposes a stored TOTP secret again after it was
first issued (see create_admin.py / seed_demo.py) — there is no API route
and no database value that gives it back to you in plaintext. This script
is the sanctioned way to get a *new* one whenever you need it: it proves
you own the account (by re-checking the account's own password) before
it will replace that account's secret and print the new one, exactly like
a real "reset my authenticator" flow.

Run it as many times as you want, for any username:

    docker compose run --rm -it backend python scripts/reset_totp.py

Each run invalidates the account's previous TOTP secret (and, since a
trusted-device skip only ever bypasses TOTP entry, never the password
check, an active trusted-device session for that account still needs no
change) and requires the account to re-enroll in an authenticator app.
"""
import asyncio
import sys
from pathlib import Path
import getpass

sys.path.insert(0, str(Path(__file__).parent.parent))

import pyotp
from sqlalchemy import select

from app.db.session import async_session_maker
from app.models import User
from app.core.security import verify_password, generate_totp_secret, get_totp_uri
from app.core.encryption import get_encryption_service


async def reset_totp():
    print("=" * 50)
    print("  Reset TOTP Secret")
    print("=" * 50)
    print()

    username = input("Username: ").strip()
    if not username:
        print("Username is required.")
        return

    password = getpass.getpass("Password (proves you own this account): ")

    enc = get_encryption_service()

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        # Same message whether the username is unknown or the password is
        # wrong - don't let this script be used to probe which usernames exist.
        if not user or not verify_password(password, user.password_hash):
            print("\n✗ Invalid username or password. Nothing was changed.")
            return

        if not user.is_active:
            print("\n✗ Account is disabled. Nothing was changed.")
            return

        new_secret = generate_totp_secret()
        user.totp_secret = enc.encrypt(new_secret, context="totp_secret")
        await session.commit()

    print(f"\n✓ TOTP secret reset for '{username}'. The old code no longer works.")
    print(f"  New secret (scan into an authenticator app now, it is never shown again): {new_secret}")
    print(f"  Provisioning URI (for a QR code):\n    {get_totp_uri(new_secret, username)}")
    print(f"  Current code (valid ~30s): {pyotp.TOTP(new_secret).now()}")


if __name__ == "__main__":
    asyncio.run(reset_totp())
