"""Complaints API Routes"""
import base64
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4, field_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint, User, ComplaintLog
from app.core.encryption import get_encryption_service
from app.core.deps import get_current_user, require_roles
from app.core.security import verify_totp
from app.core.signing import sign_payload
from app.core.log_chain import next_chain_hashes

router = APIRouter(dependencies=[Depends(get_current_user)])
enc = get_encryption_service()

VALID_STATUS_TRANSITIONS = {
    "received": ["under_investigation", "closed"],
    "under_investigation": ["received", "escalated", "closed"],
    "escalated": ["under_investigation", "closed"],
    "closed": [],
}

# "viewer" is read-only everywhere in the complaints module; every other role can act on complaints.
require_writer = require_roles("super_admin", "admin", "senior_inspector", "inspector")


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
    assigned_to_name: Optional[str]
    created_by: UUID4
    first_response_at: Optional[datetime]
    closed_at: Optional[datetime]


class StatusUpdateRequest(BaseModel):
    status: str


class AssignRequest(BaseModel):
    assigned_to: UUID4


NOTE_TYPES = ("investigation", "finding", "action")


class NoteCreateRequest(BaseModel):
    content: str
    is_confidential: bool = False
    note_type: str = "investigation"

    @field_validator("note_type")
    @classmethod
    def _validate_note_type(cls, value: str) -> str:
        return value if value in NOTE_TYPES else "investigation"


class SignRequest(BaseModel):
    totp_code: str


async def _log_activity(db: AsyncSession, complaint_id, action: str, description: str, performed_by) -> None:
    """Record an entry in the complaint's activity log (flushed with the caller's commit)"""
    created_at = datetime.utcnow()
    payload = f"{complaint_id}|{action}|{description}|{performed_by}|{created_at.isoformat()}"
    prev_hash, row_hash = await next_chain_hashes(db, ComplaintLog, payload)
    db.add(ComplaintLog(
        complaint_id=complaint_id,
        action=action,
        description=description,
        performed_by=performed_by,
        created_at=created_at,
        prev_hash=prev_hash,
        row_hash=row_hash,
    ))


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
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List complaints with optional filters, capped and paginated (default page size 200)"""
    query = select(Complaint)
    if status:
        query = query.where(Complaint.status == status)
    if priority:
        query = query.where(Complaint.priority == priority)
    query = query.order_by(Complaint.created_at.desc()).offset(max(offset, 0)).limit(min(max(limit, 1), 500))
    result = await db.execute(query)
    complaints = result.scalars().all()
    return [_serialize_complaint(c) for c in complaints]


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Create a new complaint"""
    count_result = await db.execute(select(Complaint))
    count = len(count_result.scalars().all())
    complaint_number = f"INS-{datetime.utcnow().year}-{count + 1:04d}"

    created_by = current_user.id

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
    await db.flush()
    await _log_activity(db, new_complaint.id, "created", f"Complaint received ({complaint.priority} priority)", current_user.id)
    await db.commit()
    await db.refresh(new_complaint)
    return _serialize_complaint(new_complaint)


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
async def get_complaint(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Get complaint details"""
    result = await db.execute(
        select(Complaint, User)
        .outerjoin(User, Complaint.assigned_to == User.id)
        .where(Complaint.id == complaint_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    complaint, assignee = row

    return {
        **_serialize_complaint(complaint),
        "description": enc.decrypt(complaint.description, context="description"),
        "complainant_name": enc.decrypt(complaint.complainant_name, context="complainant_name") or None,
        "complainant_phone": enc.decrypt(complaint.complainant_phone, context="complainant_phone") or None,
        "complainant_email": enc.decrypt(complaint.complainant_email, context="complainant_email") or None,
        "erp_reference_id": complaint.erp_reference_id,
        "is_anonymous": complaint.is_anonymous,
        "assigned_to": complaint.assigned_to,
        "assigned_to_name": assignee.full_name_ar if assignee else None,
        "created_by": complaint.created_by,
        "first_response_at": complaint.first_response_at,
        "closed_at": complaint.closed_at,
    }


@router.get("/{complaint_id}/history")
async def get_complaint_history(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Get the activity log (audit trail) for a complaint"""
    complaint_exists = await db.execute(select(Complaint.id).where(Complaint.id == complaint_id))
    if not complaint_exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    result = await db.execute(
        select(ComplaintLog, User)
        .outerjoin(User, ComplaintLog.performed_by == User.id)
        .where(ComplaintLog.complaint_id == complaint_id)
        .order_by(ComplaintLog.created_at.desc())
    )
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "description": log.description,
            "performed_by": user.full_name_ar if user else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log, user in result.all()
    ]


@router.patch("/{complaint_id}/status")
async def update_status(
    complaint_id: UUID4,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Update complaint status with workflow validation"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    new_status = request.status
    old_status = complaint.status
    allowed = VALID_STATUS_TRANSITIONS.get(complaint.status, [])
    if new_status not in allowed and complaint.status != new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {complaint.status} to {new_status}",
        )

    if complaint.first_response_at is None and new_status != complaint.status:
        complaint.first_response_at = datetime.utcnow()

    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()
    if new_status == "closed":
        complaint.closed_at = datetime.utcnow()
    elif complaint.status in ("received", "under_investigation") and new_status != "closed":
        complaint.closed_at = None

    if new_status != old_status:
        await _log_activity(db, complaint_id, "status_changed", f"Status changed from {old_status} to {new_status}", current_user.id)

    await db.commit()
    await db.refresh(complaint)
    return {"message": "Status updated", "complaint_id": str(complaint_id), "new_status": new_status}


@router.post("/{complaint_id}/assign")
async def assign_complaint(
    complaint_id: UUID4,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Assign complaint to a user"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    user_result = await db.execute(select(User).where(User.id == request.assigned_to))
    assignee = user_result.scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    complaint.assigned_to = request.assigned_to
    complaint.updated_at = datetime.utcnow()
    if complaint.first_response_at is None:
        complaint.first_response_at = datetime.utcnow()
    await _log_activity(db, complaint_id, "assigned", f"Assigned to {assignee.full_name_ar}", current_user.id)
    await db.commit()
    return {"message": "Complaint assigned", "complaint_id": str(complaint_id), "assigned_to": str(request.assigned_to)}


@router.post("/{complaint_id}/escalate")
async def escalate_complaint(
    complaint_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Escalate complaint priority and status"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if complaint.status not in ("received", "under_investigation"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot escalate this complaint")

    old_status = complaint.status
    complaint.status = "escalated"
    complaint.priority = "urgent"
    complaint.updated_at = datetime.utcnow()
    await _log_activity(db, complaint_id, "escalated", f"Escalated from {old_status} to urgent priority", current_user.id)
    await db.commit()
    return {"message": "Complaint escalated", "complaint_id": str(complaint_id)}


CONFIDENTIAL_NOTE_ROLES = ("senior_inspector", "admin", "super_admin")


@router.get("/{complaint_id}/notes")
async def list_notes(
    complaint_id: UUID4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List investigation notes for a complaint.

    Notes marked confidential are only visible to senior_inspector/admin/super_admin,
    or to the user who wrote them — everyone else sees a placeholder instead of the content.
    """
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
    can_see_confidential = current_user.role in CONFIDENTIAL_NOTE_ROLES
    notes = []
    for row in result.fetchall():
        is_own = row.created_by and str(row.created_by) == str(current_user.id)
        visible = not row.is_confidential or can_see_confidential or is_own
        notes.append({
            "id": str(row.id),
            "complaint_id": str(row.complaint_id),
            "content": enc.decrypt(row.note_content, context="note_content") if visible else None,
            "note_type": row.note_type,
            "is_confidential": row.is_confidential,
            "hidden": row.is_confidential and not visible,
            "created_by": str(row.created_by) if row.created_by else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    return notes


@router.post("/{complaint_id}/notes")
async def add_note(
    complaint_id: UUID4,
    request: NoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Add investigation note"""
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    created_by = current_user.id
    if complaint.first_response_at is None:
        complaint.first_response_at = datetime.utcnow()

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
            note_type=request.note_type,
            created_by=created_by,
            is_confidential=request.is_confidential,
        )
    )
    row = note_result.fetchone()
    note_kind = "confidential note" if request.is_confidential else "note"
    await _log_activity(db, complaint_id, "note_added", f"Investigation {note_kind} added ({request.note_type})", current_user.id)
    await db.commit()
    return {
        "id": str(row.id),
        "complaint_id": str(complaint_id),
        "content": request.content,
        "note_type": request.note_type,
        "is_confidential": request.is_confidential,
        "created_at": row.created_at.isoformat(),
    }


@router.post("/{complaint_id}/sign")
async def sign_report(
    complaint_id: UUID4,
    request: SignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("senior_inspector", "admin", "super_admin")),
):
    """Sign the final report with a real RSA-PSS/SHA-384 digital signature.

    Identity is re-confirmed with the signer's own current TOTP code (instead of a
    PIN shared by everyone) — this is a real re-authentication step, not a lookup.
    """
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    if complaint.status != "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only sign closed complaints")

    totp_secret = enc.decrypt(current_user.totp_secret, context="totp_secret")
    if not verify_totp(totp_secret, request.totp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication code")

    signed_at = datetime.utcnow()
    payload = f"{complaint.complaint_number}|{complaint.status}|{current_user.id}|{signed_at.isoformat()}"
    sig = sign_payload(payload)

    insert_result = await db.execute(
        text(
            """
            INSERT INTO digital_signatures (report_id, signer_id, signature_data, certificate_thumbprint, signed_at)
            VALUES (:report_id, :signer_id, :signature_data, :certificate_thumbprint, :signed_at)
            RETURNING id
            """
        ).bindparams(
            report_id=complaint_id,
            signer_id=current_user.id,
            signature_data=base64.b64decode(sig["signature"]),
            certificate_thumbprint=sig["certificate_thumbprint"],
            signed_at=signed_at,
        )
    )
    signature_id = insert_result.fetchone().id

    await _log_activity(db, complaint_id, "signed", f"Report digitally signed by {current_user.full_name_ar}", current_user.id)
    await db.commit()

    return {
        "signed": True,
        "signature_id": str(signature_id),
        "complaint_id": str(complaint_id),
        "algorithm": sig["algorithm"],
        "certificate_thumbprint": sig["certificate_thumbprint"],
        "signature": sig["signature"],
        "signed_at": signed_at.isoformat(),
    }
