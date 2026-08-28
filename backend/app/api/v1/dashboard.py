"""Dashboard API Routes"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, UUID4
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint

router = APIRouter()


class StatCard(BaseModel):
    label: str
    value: int
    color: str


class DashboardStats(BaseModel):
    total: int
    pending: int
    urgent: int
    closed: int
    by_status: dict
    by_priority: dict
    by_category: dict
    recent: List[dict]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    result = await db.execute(select(Complaint))
    complaints = result.scalars().all()

    total = len(complaints)
    pending = sum(1 for c in complaints if c.status == "under_investigation")
    urgent = sum(1 for c in complaints if c.priority == "urgent")
    closed = sum(1 for c in complaints if c.status == "closed")

    by_status = {}
    by_priority = {}
    by_category = {}
    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1

    recent = sorted(complaints, key=lambda c: c.created_at, reverse=True)[:5]

    return {
        "total": total,
        "pending": pending,
        "urgent": urgent,
        "closed": closed,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "recent": [
            {
                "id": str(c.id),
                "complaint_number": c.complaint_number,
                "title_ar": c.title_ar,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
            }
            for c in recent
        ],
    }
