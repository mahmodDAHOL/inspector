"""Audit Logs API Routes — unified system-wide activity feed (admin only)"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import ActivityLog, ComplaintLog, Complaint, User
from app.core.deps import require_roles

router = APIRouter(dependencies=[Depends(require_roles("admin", "super_admin"))])


@router.get("/logs")
async def list_logs(
    table: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List system-wide activity logs — merges complaint history with system (auth/user/department/report) activity"""
    entries = []

    if table is None or table == "complaint":
        complaint_query = (
            select(ComplaintLog, User, Complaint)
            .outerjoin(User, ComplaintLog.performed_by == User.id)
            .join(Complaint, ComplaintLog.complaint_id == Complaint.id)
        )
        if action:
            complaint_query = complaint_query.where(ComplaintLog.action == action)
        result = await db.execute(complaint_query)
        for log, user, complaint in result.all():
            entries.append({
                "id": str(log.id),
                "table_name": "complaint",
                "record_id": str(log.complaint_id),
                "context": complaint.complaint_number,
                "action": log.action,
                "description": log.description,
                "performed_by": user.full_name_ar if user else None,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            })

    if table is None or table != "complaint":
        query = select(ActivityLog, User).outerjoin(User, ActivityLog.performed_by == User.id)
        if table:
            query = query.where(ActivityLog.entity_type == table)
        if action:
            query = query.where(ActivityLog.action == action)
        result = await db.execute(query)
        for log, user in result.all():
            entries.append({
                "id": str(log.id),
                "table_name": log.entity_type,
                "record_id": str(log.entity_id) if log.entity_id else None,
                "context": None,
                "action": log.action,
                "description": log.description,
                "performed_by": user.full_name_ar if user else None,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            })

    entries.sort(key=lambda e: e["timestamp"] or "", reverse=True)

    total = len(entries)
    start = (page - 1) * per_page
    page_items = entries[start:start + per_page]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start + per_page < total,
    }
