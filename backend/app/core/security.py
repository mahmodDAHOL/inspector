"""Security utilities — Password hashing, JWT, TOTP"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
import pyotp
import base64
import hashlib
import hmac
import secrets

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> str:
    """Raise ValueError if the password is too short or too simple. Returns it unchanged otherwise."""
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters long")
    classes_present = sum([
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ])
    if classes_present < 3:
        raise ValueError("Password must mix at least 3 of: lowercase, uppercase, digits, symbols")
    return password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, get_settings().SECRET_KEY, algorithm="HS256")


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, get_settings().SECRET_KEY, algorithm="HS256")


def create_temp_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=5)
    to_encode.update({"exp": expire, "type": "temp"})
    return jwt.encode(to_encode, get_settings().SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().SECRET_KEY, algorithms=["HS256"])


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def get_totp_uri(secret: str, username: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=get_settings().TOTP_ISSUER
    )


# ---- Trusted-device tokens ("remember this device", skips TOTP only) ----
# The token itself is a fresh 256-bit server-generated random value, never a
# user-chosen secret, so a fast SHA-256 digest is the right tool here (like
# hashing an API key), not a slow salted KDF like argon2 which is for
# defending low-entropy, human-chosen passwords against offline guessing.

def generate_device_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_device_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_device_token(token), token_hash)
