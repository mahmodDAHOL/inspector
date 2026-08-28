"""Shared hash-chain helper for the append-only log tables (complaint_logs, activity_logs).

Each row's row_hash = sha256(prev_hash + this row's own fields). Walking the
chain and recomputing every hash detects any row that was altered or deleted
out of band (the DB triggers added in migration 007 block that through the
app/ORM, but a hash chain also catches direct edits made with superuser access).
"""
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def next_chain_hashes(db: AsyncSession, model_class, payload: str) -> tuple:
    """Return (prev_hash, row_hash) for a new row being appended to `model_class`."""
    result = await db.execute(
        select(model_class.row_hash).order_by(model_class.created_at.desc()).limit(1)
    )
    prev_hash = result.scalar_one_or_none()
    row_hash = hashlib.sha256(f"{prev_hash or ''}|{payload}".encode("utf-8")).hexdigest()
    return prev_hash, row_hash
