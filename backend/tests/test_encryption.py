"""Unit tests for the field-level encryption service — no database or network needed."""
import pytest

from app.core.encryption import EncryptionService

# Any valid base64 string works as a test key; production keys come from MASTER_ENCRYPTION_KEY in .env.
TEST_KEY = "dGVzdC1vbmx5LW1hc3Rlci1rZXktbmV2ZXItcHJvZC0="


@pytest.fixture
def enc():
    return EncryptionService(TEST_KEY)


def test_round_trip(enc):
    plaintext = "sensitive data — بيانات حساسة"
    ciphertext = enc.encrypt(plaintext, context="email")
    assert ciphertext != plaintext.encode("utf-8")
    assert enc.decrypt(ciphertext, context="email") == plaintext


def test_empty_string_round_trips_to_empty(enc):
    assert enc.encrypt("", context="email") == b""
    assert enc.decrypt(b"", context="email") == ""


def test_same_plaintext_encrypts_differently_each_time(enc):
    """Random IV/salt per call — ciphertext must never repeat even for identical input."""
    a = enc.encrypt("hello", context="email")
    b = enc.encrypt("hello", context="email")
    assert a != b


def test_wrong_context_fails_to_decrypt(enc):
    ciphertext = enc.encrypt("hello", context="email")
    with pytest.raises(Exception):
        enc.decrypt(ciphertext, context="phone")


def test_wrong_key_fails_to_decrypt():
    a = EncryptionService(TEST_KEY)
    b = EncryptionService("ZGlmZmVyZW50LWtleS1mb3ItdGVzdGluZy1wdXJwb3Nlcw==")
    ciphertext = a.encrypt("hello", context="email")
    with pytest.raises(Exception):
        b.decrypt(ciphertext, context="email")
