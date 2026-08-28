"""Department Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100))
    code = Column(String(20), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
