"""Trusted device model — lets a specific app install skip the TOTP step on
subsequent logins, without ever weakening the password check itself.

The device_token is a high-entropy, server-generated random secret (never a
user-chosen value), so it's hashed with a fast SHA-256 rather than argon2 —
same reasoning as JWT/API-key storage, unlike user passwords which need a
slow, salted KDF against low-entropy guessing.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    token_hash = Column(String(64), nullable=False)  # sha256 hex digest of the device secret
    label = Column(String(100))  # e.g. "Flutter Android app" — set by the client, informational only
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
