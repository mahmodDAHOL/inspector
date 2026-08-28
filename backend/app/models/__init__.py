"""Models package"""
from app.models.base import Base
from app.models.department import Department
from app.models.user import User
from app.models.complaint import Complaint

__all__ = ["Base", "Department", "User", "Complaint"]
