"""Immutable evidence files attached to complaints."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ComplaintEvidence(Base):
    __tablename__ = "complaint_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    description = Column(LargeBinary(), nullable=False)
    stored_file_name = Column(String(255), nullable=False, unique=True)
    original_file_name = Column(LargeBinary(), nullable=False)
    media_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)