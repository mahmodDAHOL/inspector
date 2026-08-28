"""User Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name_ar = Column(String(100), nullable=False)
    full_name_en = Column(String(100))
    email = Column(LargeBinary(), nullable=False)
    phone = Column(LargeBinary())
    role = Column(String(30), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    totp_secret = Column(LargeBinary(), nullable=False)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(String(10), default="0")
    locked_until = Column(DateTime)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
