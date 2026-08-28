"""Immutable Audit Logger"""
import hashlib
import json
from datetime import datetime

from app.core.encryption import get_encryption_service


class AuditLogger:
    PII_FIELDS = {"password", "totp_secret", "private_key"}

    @staticmethod
    def _hash_ip(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()[:64]

    @staticmethod
    def _sanitize_values(values: dict) -> dict:
        if not values:
            return {}
        return {k: v for k, v in values.items() if k not in AuditLogger.PII_FIELDS}

    @classmethod
    async def log(cls, conn, table_name: str, record_id: str, action: str,
                  old_values: dict = None, new_values: dict = None,
                  performed_by: str = None, ip_address: str = None,
                  user_agent: str = None, session_id: str = None):
        enc = get_encryption_service()

        old_enc = None
        if old_values:
            old_enc = enc.encrypt(json.dumps(cls._sanitize_values(old_values)), "audit")

        new_enc = None
        if new_values:
            new_enc = enc.encrypt(json.dumps(cls._sanitize_values(new_values)), "audit")

        await conn.execute(
            """INSERT INTO audit_logs 
            (table_name, record_id, action, old_values, new_values, 
             performed_by, ip_address_hash, user_agent_hash, session_id, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            table_name, record_id, action, old_enc, new_enc,
            performed_by,
            cls._hash_ip(ip_address) if ip_address else None,
            hashlib.sha256(user_agent.encode()).hexdigest()[:64] if user_agent else None,
            session_id,
            datetime.utcnow()
        )
