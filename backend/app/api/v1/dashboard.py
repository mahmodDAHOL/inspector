"""Dashboard API Routes"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, UUID4
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint, User
from app.core.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


def _response_metrics(complaints: List[Complaint]) -> dict:
    """Response-time SLA metrics: how many complaints have been acted on, and how fast"""
    total = len(complaints)
    responded = [c for c in complaints if c.first_response_at is not None]
    awaiting = total - len(responded)
    response_rate = round(len(responded) / total * 100, 1) if total else 0.0

    if responded:
        hours = [
            (c.first_response_at - c.created_at).total_seconds() / 3600
            for c in responded
            if c.created_at
        ]
        avg_response_hours = round(sum(hours) / len(hours), 1) if hours else 0.0
    else:
        avg_response_hours = 0.0

    return {
        "responded": len(responded),
        "awaiting_response": awaiting,
        "response_rate": response_rate,
        "avg_response_hours": avg_response_hours,
    }


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
    response: dict
    recent: List[dict]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    result = await db.execute(select(Complaint))
    complaints = result.scalars().all()

    users_result = await db.execute(select(User.id, User.full_name_ar))
    user_names = {row.id: row.full_name_ar for row in users_result.all()}

    total = len(complaints)
    pending = sum(1 for c in complaints if c.status == "under_investigation")
    urgent = sum(1 for c in complaints if c.priority == "urgent")
    closed = sum(1 for c in complaints if c.status == "closed")

    by_status = {}
    by_priority = {}
    by_category = {}
    by_inspector = {}
    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1
        # Only open (non-closed) complaints count toward current workload.
        if c.status != "closed":
            inspector_label = user_names.get(c.assigned_to, "غير مُسند") if c.assigned_to else "غير مُسند"
            by_inspector[inspector_label] = by_inspector.get(inspector_label, 0) + 1

    recent = sorted(complaints, key=lambda c: c.created_at, reverse=True)[:5]

    return {
        "total": total,
        "pending": pending,
        "urgent": urgent,
        "closed": closed,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "by_inspector": by_inspector,
        "response": _response_metrics(complaints),
        "recent": [
            {
                "id": str(c.id),
                "complaint_number": c.complaint_number,
                "title_ar": c.title_ar,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat(),
                "assigned_to_name": user_names.get(c.assigned_to) if c.assigned_to else None,
            }
            for c in recent
        ],
    }
