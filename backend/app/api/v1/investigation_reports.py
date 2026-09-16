"""Structured investigation report workflow."""
import base64
import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, UUID4, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.complaints import _log_activity
from app.core.deps import get_current_user, require_roles
from app.core.encryption import get_encryption_service
from app.core.security import verify_totp
from app.core.signing import sign_payload
from app.db.session import get_db
from app.models import Complaint, InvestigationReport, User

router = APIRouter(dependencies=[Depends(get_current_user)])
enc = get_encryption_service()
WRITER_ROLES = ("super_admin", "admin", "senior_inspector", "inspector")
FINALIZER_ROLES = ("super_admin", "admin", "senior_inspector")


class ReportPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=20000)
    methodology: str = Field(min_length=1, max_length=20000)
    findings: str = Field(min_length=1, max_length=30000)
    evidence_summary: str = Field(min_length=1, max_length=20000)
    conclusion: str = Field(min_length=1, max_length=20000)
    recommendations: str = Field(min_length=1, max_length=20000)

    @field_validator("title", "scope", "methodology", "findings", "evidence_summary", "conclusion", "recommendations")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Report fields must not be blank")
        return value


class FinalizeRequest(BaseModel):
    totp_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


def _serialize(report: InvestigationReport, include_signature: bool = False) -> dict:
    result = {
        "id": str(report.id),
        "complaint_id": str(report.complaint_id),
        "title": report.title,
        "scope": enc.decrypt(report.scope, context="report_scope"),
        "methodology": enc.decrypt(report.methodology, context="report_methodology"),
        "findings": enc.decrypt(report.findings, context="report_findings"),
        "evidence_summary": enc.decrypt(report.evidence_summary, context="report_evidence_summary"),
        "conclusion": enc.decrypt(report.conclusion, context="report_conclusion"),
        "recommendations": enc.decrypt(report.recommendations, context="report_recommendations"),
        "status": report.status,
        "created_by": str(report.created_by),
        "updated_by": str(report.updated_by),
        "finalized_by": str(report.finalized_by) if report.finalized_by else None,
        "finalized_at": report.finalized_at.isoformat() if report.finalized_at else None,
        "content_hash": report.content_hash,
        "signature_algorithm": report.signature_algorithm,
        "certificate_thumbprint": report.certificate_thumbprint,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }
    if include_signature and report.signature_data:
        result["signature"] = base64.b64encode(report.signature_data).decode("ascii")
    return result


async def _get_report(db: AsyncSession, complaint_id: UUID4) -> InvestigationReport:
    result = await db.execute(select(InvestigationReport).where(InvestigationReport.complaint_id == complaint_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation report not found")
    return report


@router.get("/{complaint_id}/investigation-report")
async def get_report(complaint_id: UUID4, db: AsyncSession = Depends(get_db)):
    return _serialize(await _get_report(db, complaint_id))


@router.post("/{complaint_id}/investigation-report", status_code=status.HTTP_201_CREATED)
async def create_report(
    complaint_id: UUID4,
    payload: ReportPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITER_ROLES)),
):
    complaint = await db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    existing = await db.execute(select(InvestigationReport.id).where(InvestigationReport.complaint_id == complaint_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Investigation report already exists")

    now = datetime.utcnow()
    report = InvestigationReport(
        complaint_id=complaint_id,
        title=payload.title.strip(),
        scope=enc.encrypt(payload.scope, context="report_scope"),
        methodology=enc.encrypt(payload.methodology, context="report_methodology"),
        findings=enc.encrypt(payload.findings, context="report_findings"),
        evidence_summary=enc.encrypt(payload.evidence_summary, context="report_evidence_summary"),
        conclusion=enc.encrypt(payload.conclusion, context="report_conclusion"),
        recommendations=enc.encrypt(payload.recommendations, context="report_recommendations"),
        status="draft", created_by=current_user.id, updated_by=current_user.id,
        created_at=now, updated_at=now,
    )
    db.add(report)
    await db.flush()
    await _log_activity(db, complaint_id, "report_created", "Investigation report draft created", current_user.id)
    await db.commit()
    await db.refresh(report)
    return _serialize(report)


@router.put("/{complaint_id}/investigation-report")
async def update_report(
    complaint_id: UUID4,
    payload: ReportPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*WRITER_ROLES)),
):
    report = await _get_report(db, complaint_id)
    if report.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Finalized reports are immutable")
    for field, context in (("scope", "report_scope"), ("methodology", "report_methodology"), ("findings", "report_findings"), ("evidence_summary", "report_evidence_summary"), ("conclusion", "report_conclusion"), ("recommendations", "report_recommendations")):
        setattr(report, field, enc.encrypt(getattr(payload, field), context=context))
    report.title = payload.title.strip()
    report.updated_by = current_user.id
    report.updated_at = datetime.utcnow()
    await _log_activity(db, complaint_id, "report_updated", "Investigation report draft updated", current_user.id)
    await db.commit()
    await db.refresh(report)
    return _serialize(report)


@router.post("/{complaint_id}/investigation-report/finalize")
async def finalize_report(
    complaint_id: UUID4,
    request: FinalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*FINALIZER_ROLES)),
):
    complaint = await db.get(Complaint, complaint_id)
    report = await _get_report(db, complaint_id)
    if complaint.status != "closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint must be closed before finalizing the report")
    if report.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report is already finalized")
    secret = enc.decrypt(current_user.totp_secret, context="totp_secret")
    if not verify_totp(secret, request.totp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication code")

    finalized_at = datetime.utcnow()
    fields = [
        report.title,
        enc.decrypt(report.scope, context="report_scope"),
        enc.decrypt(report.methodology, context="report_methodology"),
        enc.decrypt(report.findings, context="report_findings"),
        enc.decrypt(report.evidence_summary, context="report_evidence_summary"),
        enc.decrypt(report.conclusion, context="report_conclusion"),
        enc.decrypt(report.recommendations, context="report_recommendations"),
    ]
    content_hash = hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest()
    canonical = "|".join([str(report.id), str(report.complaint_id), content_hash, str(current_user.id), finalized_at.isoformat()])
    signature = sign_payload(canonical)
    report.status = "final"
    report.finalized_by = current_user.id
    report.updated_by = current_user.id
    report.finalized_at = finalized_at
    report.updated_at = finalized_at
    report.content_hash = content_hash
    report.signature_data = base64.b64decode(signature["signature"])
    report.signature_algorithm = signature["algorithm"]
    report.certificate_thumbprint = signature["certificate_thumbprint"]
    await _log_activity(db, complaint_id, "report_finalized", f"Investigation report finalized by {current_user.full_name_ar}", current_user.id)
    await db.commit()
    await db.refresh(report)
    return {**_serialize(report, include_signature=True)}