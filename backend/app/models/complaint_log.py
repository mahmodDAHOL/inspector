"""Complaint Activity Log Model — per-complaint history/audit trail"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ComplaintLog(Base):
    __tablename__ = "complaint_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(30), nullable=False)
    description = Column(String(300), nullable=False)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Hash chain (tamper-evidence): row_hash = sha256(prev_hash + this row's fields).
    # The table also rejects UPDATE/DELETE at the database level (see migration 007).
    prev_hash = Column(String(64))
    row_hash = Column(String(64))
