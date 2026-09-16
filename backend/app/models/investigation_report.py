"""Structured investigation report linked to one complaint."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    scope = Column(LargeBinary(), nullable=False)
    methodology = Column(LargeBinary(), nullable=False)
    findings = Column(LargeBinary(), nullable=False)
    evidence_summary = Column(LargeBinary(), nullable=False)
    conclusion = Column(LargeBinary(), nullable=False)
    recommendations = Column(LargeBinary(), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    finalized_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    finalized_at = Column(DateTime)
    content_hash = Column(String(64))
    signature_data = Column(LargeBinary())
    signature_algorithm = Column(String(40))
    certificate_thumbprint = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)