"""External API — MediaGate Integration"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class ComplaintPollItem(BaseModel):
    erp_reference_id: str
    title_ar: str
    description: str
    category: str
    priority: str
    submitted_at: str


class StatusPushRequest(BaseModel):
    mediagate_complaint_id: str
    inspection_complaint_number: str
    status: str
    status_ar: str
    status_en: str
    updated_at: str
    can_be_escalated: bool = False


@router.get("/poll/complaints")
async def poll_complaints(
    since: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_signature: str = Header(None, alias="X-Signature")
):
    """Poll MediaGate for new complaints"""
    return {
        "complaints": [
            {
                "erp_reference_id": "ERP-2026-0891",
                "title_ar": "مخالفة في إجراءات التعاقد",
                "description": "تم التعاقد دون إجراء مناقصة علنية",
                "category": "procurement_violation",
                "priority": "urgent",
                "submitted_at": "2026-08-25T09:15:00Z"
            }
        ],
        "pagination": {"total": 1, "page": page, "per_page": per_page}
    }


@router.post("/push/status")
async def push_status(request: StatusPushRequest):
    """Push status update to MediaGate"""
    return {"message": "Status pushed successfully", "mediagate_id": request.mediagate_complaint_id}


@router.get("/complaints/{complaint_number}/status")
async def get_status(complaint_number: str):
    """Get complaint status for MediaGate"""
    return {
        "complaint_number": complaint_number,
        "status": "under_investigation",
        "status_ar": "قيد التحقيق",
        "status_en": "Under Investigation",
        "updated_at": "2026-08-29T09:00:00Z"
    }
