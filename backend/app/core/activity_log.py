"""System-wide activity logging helper — records who did what, for the Audit Log page"""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog
from app.core.log_chain import next_chain_hashes


async def log_activity(db: AsyncSession, entity_type: str, action: str, description: str, performed_by=None, entity_id=None) -> None:
    """Queue an activity log entry. Flushed/committed together with the caller's own change."""
    created_at = datetime.utcnow()
    payload = f"{entity_type}|{entity_id}|{action}|{description}|{performed_by}|{created_at.isoformat()}"
    prev_hash, row_hash = await next_chain_hashes(db, ActivityLog, payload)
    db.add(ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        performed_by=performed_by,
        created_at=created_at,
        prev_hash=prev_hash,
        row_hash=row_hash,
    ))
