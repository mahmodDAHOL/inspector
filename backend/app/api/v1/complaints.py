"""Complaints API Routes"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, UUID4
from typing import List, Optional

router = APIRouter()


class ComplaintCreate(BaseModel):
    title_ar: str
    title_en: Optional[str] = None
    description: str
    category: str
    priority: str = "normal"
    source: str = "Direct"
    is_anonymous: bool = False
    complainant_name: Optional[str] = None
    complainant_phone: Optional[str] = None
    complainant_email: Optional[str] = None
    erp_reference_id: Optional[str] = None


class ComplaintResponse(BaseModel):
    id: UUID4
    complaint_number: str
    title_ar: str
    status: str
    priority: str
    category: str


@router.get("", response_model=List[ComplaintResponse])
async def list_complaints(status: Optional[str] = None, priority: Optional[str] = None):
    """List all complaints"""
    return [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "complaint_number": "INS-2026-0891",
            "title_ar": "مخالفة في إجراءات التعاقد",
            "status": "under_investigation",
            "priority": "urgent",
            "category": "procurement_violation"
        }
    ]


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(complaint: ComplaintCreate):
    """Create a new complaint"""
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "complaint_number": "INS-2026-0892",
        "title_ar": complaint.title_ar,
        "status": "received",
        "priority": complaint.priority,
        "category": complaint.category
    }


@router.get("/{complaint_id}")
async def get_complaint(complaint_id: UUID4):
    """Get complaint details"""
    return {
        "id": str(complaint_id),
        "complaint_number": "INS-2026-0891",
        "title_ar": "مخالفة في إجراءات التعاقد",
        "description": "تم التعاقد دون إجراء مناقصة علنية",
        "status": "under_investigation",
        "priority": "urgent",
        "category": "procurement_violation",
        "assigned_to": "inspector_ahmed",
        "created_at": "2026-08-25T09:15:00Z"
    }


@router.patch("/{complaint_id}/status")
async def update_status(complaint_id: UUID4, status: str):
    """Update complaint status"""
    return {"message": "Status updated", "complaint_id": str(complaint_id), "new_status": status}


@router.post("/{complaint_id}/notes")
async def add_note(complaint_id: UUID4, content: str, is_confidential: bool = False):
    """Add investigation note"""
    return {"id": "note-uuid", "complaint_id": str(complaint_id), "content": content}


@router.post("/{complaint_id}/sign")
async def sign_report(complaint_id: UUID4, pin: str):
    """Sign final report with digital signature"""
    return {
        "signed": True,
        "complaint_id": str(complaint_id),
        "algorithm": "RSA-PSS-SHA384",
        "signed_at": "2026-08-28T14:30:00Z"
    }
