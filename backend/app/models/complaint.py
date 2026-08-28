"""Complaint Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number = Column(String(20), unique=True, nullable=False)
    title_ar = Column(String(200), nullable=False)
    title_en = Column(String(200))
    description = Column(LargeBinary(), nullable=False)
    complainant_name = Column(LargeBinary())
    complainant_phone = Column(LargeBinary())
    complainant_email = Column(LargeBinary())
    source = Column(String(10), nullable=False)
    category = Column(String(30), nullable=False)
    priority = Column(String(10), nullable=False)
    status = Column(String(30), default="received", nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    erp_reference_id = Column(String(50))
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    first_response_at = Column(DateTime)
