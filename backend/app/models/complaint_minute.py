"""Complaint minute model — investigation minutes (محضر تحقيق) and meeting
minutes (محضر اجتماع), each tied to one complaint and carrying exactly one
PDF attachment (the signed/scanned original — the record of what was said
in a session, not something meant to be edited after the fact).

`summary` and `attendees` hold free text about real people and what they
said, so they're encrypted at rest the same way investigation note content
and complainant details are — see EncryptionService.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ComplaintMinute(Base):
    __tablename__ = "complaint_minutes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    minute_type = Column(String(20), nullable=False)  # 'investigation' | 'meeting'
    title = Column(String(200), nullable=False)
    minute_date = Column(DateTime, nullable=False)
    attendees = Column(LargeBinary())
    summary = Column(LargeBinary(), nullable=False)
    # The PDF itself lives on disk under UPLOAD_DIR, named by `stored_file_name`
    # (a fresh UUID, never the client-supplied name) — `original_file_name` is
    # kept only for display and for the Content-Disposition on download.
    stored_file_name = Column(String(255), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
