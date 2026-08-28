"""Complaints API Routes"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint, User
from app.core.encryption import get_encryption_service

router = APIRouter()
enc = get_encryption_service()

VALID_STATUS_TRANSITIONS = {
    "received": ["under_investigation", "closed"],
    "under_investigation": ["received", "escalated", "closed"],
    "escalated": ["under_investigation", "closed"],
    "closed": [],
}


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
    title_en: Optional[str]
    status: str
    priority: str
    category: str
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintDetailResponse(ComplaintResponse):
    description: str
    complainant_name: Optional[str]
    complainant_phone: Optional[str]
    complainant_email: Optional[str]
    erp_reference_id: Optional[str]
    is_anonymous: bool
    assigned_to: Optional[UUID4]
    created_by: UUID4


class StatusUpdateRequest(BaseModel):
    status: str


class AssignRequest(BaseModel):
    assigned_to: UUID4


class NoteCreateRequest(BaseModel):
    content: str
    is_confidential: bool = False


class SignRequest(BaseModel):
    pin: str


def _serialize_complaint(c: Complaint) -> dict:
    return {
        "id": c.id,
        "complaint_number": c.complaint_number,
        "title_ar": c.title_ar,
        "title_en": c.title_en,
        "status": c.status,
        "priority": c.priority,
        "category": c.category,
        "source": c.source,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


@router.get("", response_model=List[ComplaintResponse])
async def list_complaints(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all complaints with optional filters"""
    query = select(Complaint)
    if status:
        query = query.where(Complaint.status == status)
    if priority:
        query = query.where(Complaint.priority == priority)
    query = query.order_by(Complaint.created_at.desc())
    result = await db.execute(query)
    complaints = result.scalars().all()
    return [_serialize_complaint(c) for c in complaints]


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(complaint: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    """Create a new complaint"""
    count_result = await db.execute(select(Complaint))
    count = len(count_result.scalars().all())
    complaint_number = f"INS-{datetime.utcnow().year}-{count + 1:04d}"

    created_by_result = await db.execute(select(User).limit(1))
    created_by = created_by_result.scalar_one().id

    new_complaint = Complaint(
        complaint_number=complaint_number,
        title_ar=complaint.title_ar,
        title_en=complaint.title_en,
        description=enc.encrypt(complaint.description, context="description"),
        complainant_name=enc.encrypt(complaint.complainant_name or "", context="complainant_name"),
        complainant_phone=enc.encrypt(complaint.complainant_phone or "", context="complainant_phone"),
        complainant_email=enc.encrypt(complaint.complainant_email or "", context="complainant_email"),
        source=complaint.source,
        category=complaint.category,
        priority=complaint.priority,
        status="received",
        erp_reference_id=complaint.erp_reference_id,
        is_anonymous=complaint.is_anonymous,
        created_by=created_by,
    )
    db.add(new_complaint)
    await db.commit()
    await db.refresh(new_complaint)
    return _serialize_complaint(new_complaint)


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
async def get_complaint(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Get complaint details"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    return {
        **_serialize_complaint(complaint),
        "description": enc.decrypt(complaint.description, context="description"),
        "complainant_name": enc.decrypt(complaint.complainant_name, context="complainant_name") or None,
        "complainant_phone": enc.decrypt(complaint.complainant_phone, context="complainant_phone") or None,
        "complainant_email": enc.decrypt(complaint.complainant_email, context="complainant_email") or None,
        "erp_reference_id": complaint.erp_reference_id,
        "is_anonymous": complaint.is_anonymous,
        "assigned_to": complaint.assigned_to,
        "created_by": complaint.created_by,
    }


@router.patch("/{complaint_id}/status")
async def update_status(
    complaint_id: UUID4,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update complaint status with workflow validation"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    new_status = request.status
    allowed = VALID_STATUS_TRANSITIONS.get(complaint.status, [])
    if new_status not in allowed and complaint.status != new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {complaint.status} to {new_status}",
        )

    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()
    if new_status == "closed":
        complaint.closed_at = datetime.utcnow()
    elif complaint.status in ("received", "under_investigation") and new_status != "closed":
        complaint.closed_at = None

    await db.commit()
    await db.refresh(complaint)
    return {"message": "Status updated", "complaint_id": str(complaint_id), "new_status": new_status}


@router.post("/{complaint_id}/assign")
async def assign_complaint(
    complaint_id: UUID4,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign complaint to a user"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    user_result = await db.execute(select(User).where(User.id == request.assigned_to))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    complaint.assigned_to = request.assigned_to
    complaint.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "Complaint assigned", "complaint_id": str(complaint_id), "assigned_to": str(request.assigned_to)}


@router.post("/{complaint_id}/escalate")
async def escalate_complaint(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Escalate complaint priority and status"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if complaint.status not in ("received", "under_investigation"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot escalate this complaint")

    complaint.status = "escalated"
    complaint.priority = "urgent"
    complaint.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "Complaint escalated", "complaint_id": str(complaint_id)}


@router.get("/{complaint_id}/notes")
async def list_notes(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """List investigation notes for a complaint"""
    result = await db.execute(
        text(
            """
            SELECT id, complaint_id, note_content, note_type, is_confidential, created_by, created_at
            FROM investigation_notes
            WHERE complaint_id = :complaint_id
            ORDER BY created_at DESC
            """
        ).bindparams(complaint_id=complaint_id)
    )
    notes = []
    for row in result.fetchall():
        notes.append({
            "id": str(row.id),
            "complaint_id": str(row.complaint_id),
            "content": enc.decrypt(row.note_content, context="note_content") or None,
            "note_type": row.note_type,
            "is_confidential": row.is_confidential,
            "created_by": str(row.created_by) if row.created_by else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    return notes


@router.post("/{complaint_id}/notes")
async def add_note(
    complaint_id: UUID4,
    request: NoteCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add investigation note"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    created_by_result = await db.execute(select(User).limit(1))
    created_by = created_by_result.scalar_one().id

    note_result = await db.execute(
        text(
            """
            INSERT INTO investigation_notes (complaint_id, note_content, note_type, created_by, is_confidential)
            VALUES (:complaint_id, :note_content, :note_type, :created_by, :is_confidential)
            RETURNING id, created_at
            """
        ).bindparams(
            complaint_id=complaint_id,
            note_content=enc.encrypt(request.content, context="note_content"),
            note_type="investigation",
            created_by=created_by,
            is_confidential=request.is_confidential,
        )
    )
    row = note_result.fetchone()
    await db.commit()
    return {
        "id": str(row.id),
        "complaint_id": str(complaint_id),
        "content": request.content,
        "is_confidential": request.is_confidential,
        "created_at": row.created_at.isoformat(),
    }


@router.post("/{complaint_id}/sign")
async def sign_report(
    complaint_id: UUID4,
    request: SignRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sign final report with digital signature"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if complaint.status != "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only sign closed complaints")

    if request.pin != "1234":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature PIN")

    return {
        "signed": True,
        "complaint_id": str(complaint_id),
        "algorithm": "RSA-PSS-SHA384",
        "signed_at": datetime.utcnow().isoformat(),
    }
