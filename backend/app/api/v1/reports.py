"""Reports API Routes"""
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint

router = APIRouter()


class SummaryRequest(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None


@router.post("/summary")
async def generate_summary(request: SummaryRequest, db: AsyncSession = Depends(get_db)):
    """Generate complaints summary report"""
    query = select(Complaint)

    if request.from_date:
        from_dt = datetime.fromisoformat(request.from_date).replace(hour=0, minute=0, second=0)
        query = query.where(Complaint.created_at >= from_dt)
    if request.to_date:
        to_dt = datetime.fromisoformat(request.to_date).replace(hour=23, minute=59, second=59)
        query = query.where(Complaint.created_at <= to_dt)

    result = await db.execute(query)
    complaints = result.scalars().all()

    by_status = {}
    by_priority = {}
    by_category = {}
    for c in complaints:
        by_status[c.status] = by_status.get(c.status, 0) + 1
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
        by_category[c.category] = by_category.get(c.category, 0) + 1

    return {
        "report_id": f"RPT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "total_complaints": len(complaints),
        "date_range": {
            "from": request.from_date,
            "to": request.to_date,
        },
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
    }


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download report as JSON placeholder (PDF generation requires additional library)"""
    return {
        "message": "Report download endpoint",
        "report_id": report_id,
        "note": "PDF export requires a reporting library such as WeasyPrint or ReportLab",
    }
