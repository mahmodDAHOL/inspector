"""Complaint Minutes API Routes — investigation minutes (محضر تحقيق) and
meeting minutes (محضر اجتماع), each linked to a complaint with one PDF
attachment (the signed/scanned session record).
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field, UUID4
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
require_archiver = require_roles("super_admin", "admin", "senior_inspector")


class ArchiveMinuteRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

MINUTE_TYPES = ("investigation", "meeting")


def _minutes_dir(complaint_id) -> str:
    path = os.path.join(settings.UPLOAD_DIR, "minutes", str(complaint_id))
    os.makedirs(path, exist_ok=True)
    return path


def _attendee_dir(complaint_id, minute_id) -> str:
    path = os.path.join(_minutes_dir(complaint_id), "attendees", str(minute_id))
    os.makedirs(path, exist_ok=True)
    return path


def _parse_attendees(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [{"name": value}]
    except (TypeError, json.JSONDecodeError):
        return [{"name": value}]


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
                       m.original_file_name, m.file_size_bytes, m.created_at, m.archived_at, m.archived_reason,
                     u.full_name_ar AS uploaded_by_name, a.full_name_ar AS archived_by_name
            FROM complaint_minutes m
              LEFT JOIN users u ON u.id = m.uploaded_by
              LEFT JOIN users a ON a.id = m.archived_by
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
            "attendees": _parse_attendees(enc.decrypt(row.attendees, context="minute_attendees")),
            "summary": enc.decrypt(row.summary, context="minute_summary"),
            "original_file_name": row.original_file_name,
            "file_size_bytes": row.file_size_bytes,
            "uploaded_by_name": row.uploaded_by_name,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
            "archived_by_name": row.archived_by_name,
            "archived_reason": enc.decrypt(row.archived_reason, context="minute_archived_reason") if row.archived_reason else None,
        }
        for row in result.fetchall()
    ]


@router.post("/{complaint_id}/minutes/{minute_id}/archive")
async def archive_minute(
    complaint_id: UUID4,
    minute_id: UUID4,
    request: ArchiveMinuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_archiver),
):
    reason = request.reason.strip()
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancellation reason is required")
    result = await db.execute(
        text("SELECT id, title, archived_at FROM complaint_minutes WHERE id = :minute_id AND complaint_id = :complaint_id")
        .bindparams(minute_id=minute_id, complaint_id=complaint_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minute not found")
    if row.archived_at:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Minute is already archived")
    archived_at = datetime.utcnow()
    await db.execute(
        text("UPDATE complaint_minutes SET archived_at = :archived_at, archived_by = :archived_by, archived_reason = :archived_reason WHERE id = :minute_id AND complaint_id = :complaint_id")
        .bindparams(archived_at=archived_at, archived_by=current_user.id, archived_reason=enc.encrypt(reason, context="minute_archived_reason"), minute_id=minute_id, complaint_id=complaint_id)
    )
    await _log_activity(db, complaint_id, "minute_archived", f"Minute cancelled: {row.title}", current_user.id)
    await db.commit()
    return {"id": str(minute_id), "archived_at": archived_at.isoformat(), "archived_by_name": current_user.full_name_ar, "archived_reason": reason}


@router.post("/{complaint_id}/minutes", status_code=status.HTTP_201_CREATED)
async def create_minute(
    complaint_id: UUID4,
    minute_type: str = Form(...),
    title: str = Form(...),
    minute_date: str = Form(...),
    summary: str = Form(...),
    attendees: str = Form("[]"),
    file: UploadFile = File(...),
    id_images: List[UploadFile] = File(default=[]),
    id_image_indices: str = Form("[]"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    """Upload a new investigation/meeting minute with its PDF attachment"""
    await _get_complaint_or_404(db, complaint_id)

    try:
        attendee_rows = json.loads(attendees or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attendees data")
    if not isinstance(attendee_rows, list) or len(attendee_rows) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attendees data")
    try:
        image_indices = json.loads(id_image_indices or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID image mapping")
    if len(image_indices) != len(id_images) or any(not isinstance(index, int) or index < 0 or index >= len(attendee_rows) for index in image_indices):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID image mapping")
    for attendee in attendee_rows:
        if not isinstance(attendee, dict) or not attendee.get("name", "").strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Each attendee must have a name")

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
    attendee_dir = _attendee_dir(complaint_id, minute_id)
    saved_images = []
    try:
        for image, index in zip(id_images, image_indices):
            image_type = (image.content_type or "").lower()
            if image_type not in ("image/jpeg", "image/png"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID images must be JPEG or PNG")
            image_content = await image.read(settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
            if len(image_content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID image exceeds the file size limit")
            signature = b"\xff\xd8\xff" if image_type == "image/jpeg" else b"\x89PNG\r\n\x1a\n"
            if not image_content.startswith(signature):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID image content does not match its type")
            image_name = f"{uuid.uuid4()}.{'jpg' if image_type == 'image/jpeg' else 'png'}"
            with open(os.path.join(attendee_dir, image_name), "wb") as image_file:
                image_file.write(image_content)
            saved_images.append(image_name)
            attendee_rows[index]["id_image"] = True
            attendee_rows[index]["id_image_file"] = image_name
    except Exception:
        for image_name in saved_images:
            try:
                os.remove(os.path.join(attendee_dir, image_name))
            except FileNotFoundError:
                pass
        os.remove(dest_path)
        raise
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
            attendees=enc.encrypt(json.dumps(attendee_rows, ensure_ascii=False), context="minute_attendees"),
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
        "attendees": attendee_rows,
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


@router.get("/{complaint_id}/minutes/{minute_id}/attendee/{attendee_index}/id-image")
async def download_attendee_id_image(complaint_id: UUID4, minute_id: UUID4, attendee_index: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT attendees FROM complaint_minutes WHERE id = :minute_id AND complaint_id = :complaint_id").bindparams(minute_id=minute_id, complaint_id=complaint_id))
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Minute not found")
    attendees = _parse_attendees(enc.decrypt(row.attendees, context="minute_attendees"))
    if attendee_index < 0 or attendee_index >= len(attendees) or not attendees[attendee_index].get("id_image"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID image not found")
    directory = _attendee_dir(complaint_id, minute_id)
    image_name = attendees[attendee_index].get("id_image_file")
    if not image_name or os.path.basename(image_name) != image_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID image file missing")
    path = os.path.join(directory, image_name)
    if not os.path.isfile(path) or not path.endswith((".jpg", ".png")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID image file missing")
    media_type = "image/png" if path.endswith(".png") else "image/jpeg"
    with open(path, "rb") as image_file:
        return Response(content=image_file.read(), media_type=media_type, headers={"Content-Disposition": "inline"})
