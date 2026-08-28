"""Unit tests for password hashing, TOTP, and password strength rules."""
import pytest
import pyotp

from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    generate_totp_secret,
    verify_totp,
)


def test_password_hash_round_trip():
    hashed = get_password_hash("CorrectHorse9!")
    assert verify_password("CorrectHorse9!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_totp_round_trip():
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code)
    assert not verify_totp(secret, "000000")


@pytest.mark.parametrize("password", [
    "short1!",           # too short
    "alllowercase123",   # only 2 character classes (lower + digit)
    "ALLUPPERCASE123",   # only 2 character classes
    "",
])
def test_weak_passwords_rejected(password):
    with pytest.raises(ValueError):
        validate_password_strength(password)


@pytest.mark.parametrize("password", [
    "Str0ng!Passw0rd",
    "correct-Horse-Battery9",
])
def test_strong_passwords_accepted(password):
    assert validate_password_strength(password) == password
