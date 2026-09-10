"""Complaint Minutes API Routes — investigation minutes (محضر تحقيق) and
meeting minutes (محضر اجتماع), each linked to a complaint with one PDF
attachment (the signed/scanned session record).
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import UUID4
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Complaint, User
from app.core.config import get_settings
from app.core.encryption import get_encryption_service
from app.core.deps import get_current_user, require_roles
from app.api.v1.complaints import _log_activity

router = APIRouter(dependencies=[Depends(get_current_user)])
enc = get_encryption_service()
settings = get_settings()

require_writer = require_roles("super_admin", "admin", "senior_inspector", "inspector")

MINUTE_TYPES = ("investigation", "meeting")


def _minutes_dir(complaint_id) -> str:
    path = os.path.join(settings.UPLOAD_DIR, "minutes", str(complaint_id))
    os.makedirs(path, exist_ok=True)
    return path


async def _get_complaint_or_404(db: AsyncSession, complaint_id) -> Complaint:
    result = await db.execute(select(Complaint.id).where(Complaint.id == complaint_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")


@router.get("/{complaint_id}/minutes")
async def list_minutes(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    """List investigation/meeting minutes for a complaint (metadata + decrypted text, not the PDF bytes)"""
    await _get_complaint_or_404(db, complaint_id)

    result = await db.execute(
        text(
            """
            SELECT m.id, m.minute_type, m.title, m.minute_date, m.attendees, m.summary,
                   m.original_file_name, m.file_size_bytes, m.created_at, u.full_name_ar AS uploaded_by_name
            FROM complaint_minutes m
            LEFT JOIN users u ON u.id = m.uploaded_by
            WHERE m.complaint_id = :complaint_id
            ORDER BY m.minute_date DESC, m.created_at DESC
            """
        ).bindparams(complaint_id=complaint_id)
    )
    return [
        {
            "id": str(row.id),
            "minute_type": row.minute_type,
            "title": row.title,
            "minute_date": row.minute_date.isoformat() if row.minute_date else None,
            "attendees": enc.decrypt(row.attendees, context="minute_attendees") if row.attendees else None,
            "summary": enc.decrypt(row.summary, context="minute_summary"),
            "original_file_name": row.original_file_name,
            "file_size_bytes": row.file_size_bytes,
            "uploaded_by_name": row.uploaded_by_name,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in result.fetchall()
    ]


@router.post("/{complaint_id}/minutes", status_code=status.HTTP_201_CREATED)
async def create_minute(
    complaint_id: UUID4,
    minute_type: str = Form(...),
    title: str = Form(...),
    minute_date: str = Form(...),
    summary: str = Form(...),
    attendees: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Upload a new investigation/meeting minute with its PDF attachment"""
    await _get_complaint_or_404(db, complaint_id)

    if minute_type not in MINUTE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid minute_type")

    try:
        parsed_date = datetime.fromisoformat(minute_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid minute_date")

    original_name = file.filename or "minute.pdf"
    is_pdf = (file.content_type == "application/pdf") or original_name.lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF attachments are allowed")

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    stored_name = f"{uuid.uuid4()}.pdf"
    dest_path = os.path.join(_minutes_dir(complaint_id), stored_name)
    with open(dest_path, "wb") as f:
        f.write(content)

    minute_id = uuid.uuid4()
    insert_result = await db.execute(
        text(
            """
            INSERT INTO complaint_minutes
                (id, complaint_id, minute_type, title, minute_date, attendees, summary,
                 stored_file_name, original_file_name, file_size_bytes, uploaded_by, created_at)
            VALUES
                (:id, :complaint_id, :minute_type, :title, :minute_date, :attendees, :summary,
                 :stored_file_name, :original_file_name, :file_size_bytes, :uploaded_by, :created_at)
            RETURNING created_at
            """
        ).bindparams(
            id=minute_id,
            complaint_id=complaint_id,
            minute_type=minute_type,
            title=title,
            minute_date=parsed_date,
            attendees=enc.encrypt(attendees, context="minute_attendees") if attendees else None,
            summary=enc.encrypt(summary, context="minute_summary"),
            stored_file_name=stored_name,
            original_file_name=original_name,
            file_size_bytes=len(content),
            uploaded_by=current_user.id,
            created_at=datetime.utcnow(),
        )
    )
    row = insert_result.fetchone()

    kind_label = "محضر تحقيق" if minute_type == "investigation" else "محضر اجتماع"
    await _log_activity(db, complaint_id, "minute_added", f"{kind_label} أُضيف: {title}", current_user.id)
    await db.commit()

    return {
        "id": str(minute_id),
        "minute_type": minute_type,
        "title": title,
        "minute_date": parsed_date.isoformat(),
        "attendees": attendees,
        "summary": summary,
        "original_file_name": original_name,
        "file_size_bytes": len(content),
        "uploaded_by_name": current_user.full_name_ar,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/{complaint_id}/minutes/{minute_id}/file")
async def download_minute_file(complaint_id: UUID4, minute_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Stream the PDF attachment for one minute"""
    result = await db.execute(
        text(
            """
            SELECT stored_file_name, original_file_name
            FROM complaint_minutes
            WHERE id = :minute_id AND complaint_id = :complaint_id
            """
        ).bindparams(minute_id=minute_id, complaint_id=complaint_id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minute not found")

    path = os.path.join(_minutes_dir(complaint_id), row.stored_file_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file missing on disk")

    with open(path, "rb") as f:
        data = f.read()

    safe_name = row.original_file_name.replace('"', "")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )
