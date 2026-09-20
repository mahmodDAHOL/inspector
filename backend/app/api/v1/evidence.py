"""Secure, append-only complaint evidence files."""
import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.complaints import _log_activity
from app.core.config import get_settings
from app.core.deps import get_current_user, require_roles
from app.core.encryption import get_encryption_service
from app.db.session import get_db
from app.models import Complaint, ComplaintEvidence, User

router = APIRouter(dependencies=[Depends(get_current_user)])
settings = get_settings()
enc = get_encryption_service()
WRITER_ROLES = ("super_admin", "admin", "senior_inspector", "inspector")
MAX_FILENAME_LENGTH = 180
ALLOWED_TYPES = {
    "application/pdf": (b"%PDF-",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}


def _evidence_dir(complaint_id) -> Path:
    path = Path(settings.UPLOAD_DIR) / "evidence" / str(complaint_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_original_name(filename: str) -> str:
    name = os.path.basename(filename).replace("\x00", "").strip()
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)
    return (name or "evidence")[:MAX_FILENAME_LENGTH]


def _serialize(item: ComplaintEvidence, uploader_name: Optional[str]) -> dict:
    return {
        "id": str(item.id),
        "complaint_id": str(item.complaint_id),
        "description": enc.decrypt(item.description, context="evidence_description"),
        "original_file_name": enc.decrypt(item.original_file_name, context="evidence_filename"),
        "media_type": item.media_type,
        "file_size_bytes": item.file_size_bytes,
        "sha256": item.sha256,
        "uploaded_by_name": uploader_name,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/{complaint_id}/evidence")
async def list_evidence(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    complaint = await db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    result = await db.execute(
        select(ComplaintEvidence, User.full_name_ar)
        .join(User, ComplaintEvidence.uploaded_by == User.id)
        .where(ComplaintEvidence.complaint_id == complaint_id)
        .order_by(ComplaintEvidence.created_at.desc())
    )
    return [_serialize(item, name) for item, name in result.all()]


@router.post("/{complaint_id}/evidence", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    complaint_id: UUID4,
    description: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITER_ROLES)),
):
    complaint = await db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if not description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evidence description is required")

    media_type = (file.content_type or "").lower()
    signatures = ALLOWED_TYPES.get(media_type)
    if not signatures:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, JPEG, and PNG evidence files are allowed")

    content = await file.read(settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty evidence file")
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
    if not any(content.startswith(signature) for signature in signatures):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content does not match its declared type")

    evidence_id = uuid.uuid4()
    stored_name = f"{evidence_id}.bin"
    destination = _evidence_dir(complaint_id) / stored_name
    destination.write_bytes(content)
    item = ComplaintEvidence(
        id=evidence_id,
        complaint_id=complaint_id,
        description=enc.encrypt(description.strip(), context="evidence_description"),
        original_file_name=enc.encrypt(_safe_original_name(file.filename or "evidence"), context="evidence_filename"),
        stored_file_name=stored_name,
        media_type=media_type,
        file_size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        uploaded_by=current_user.id,
    )
    db.add(item)
    await _log_activity(db, complaint_id, "evidence_added", f"Evidence added: {_safe_original_name(file.filename or 'evidence')}", current_user.id)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        destination.unlink(missing_ok=True)
        raise
    await db.refresh(item)
    return _serialize(item, current_user.full_name_ar)


@router.get("/{complaint_id}/evidence/{evidence_id}/file")
async def download_evidence(complaint_id: UUID4, evidence_id: UUID4, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplaintEvidence).where(
            ComplaintEvidence.id == evidence_id,
            ComplaintEvidence.complaint_id == complaint_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    path = _evidence_dir(complaint_id) / item.stored_file_name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file missing on disk")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != item.sha256:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Evidence integrity check failed")
    filename = enc.decrypt(item.original_file_name, context="evidence_filename").replace('"', "")
    return Response(content=data, media_type=item.media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Content-SHA256": item.sha256})