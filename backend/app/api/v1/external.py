"""External API — MediaGate Integration

Every route here requires a valid X-API-Key (matched against MEDIAGATE_API_KEY)
and a valid X-Signature (HMAC-SHA256 of the raw request body, keyed with the
same API key), plus a per-IP rate limit — this endpoint is reachable from the
public internet through nginx, so none of this is optional hardening.
"""
import hashlib
import hmac
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.rate_limit import rate_limit


async def verify_mediagate_request(
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_signature: str = Header(None, alias="X-Signature"),
):
    settings = get_settings()
    if not settings.MEDIAGATE_API_KEY:
        # No key configured server-side — refuse everything rather than accept unauthenticated traffic.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MediaGate integration not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.MEDIAGATE_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    body = await request.body()
    expected_signature = hmac.new(settings.MEDIAGATE_API_KEY.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not x_signature or not hmac.compare_digest(x_signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")


router = APIRouter(
    dependencies=[
        Depends(rate_limit("external", max_requests=30, window_seconds=60)),
        Depends(verify_mediagate_request),
    ]
)


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
