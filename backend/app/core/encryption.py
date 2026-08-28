"""AES-256-GCM Field-Level Encryption Service"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

from app.core.config import get_settings


class EncryptionService:
    def __init__(self, master_key: str):
        self._master_key = base64.b64decode(master_key)

    def _derive_key(self, salt: bytes, context: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt + context.encode(),
            iterations=100000,
        )
        return kdf.derive(self._master_key)

    def encrypt(self, plaintext: str, context: str = "default") -> bytes:
        if not plaintext:
            return b""
        iv = os.urandom(12)
        salt = os.urandom(16)
        key = self._derive_key(salt, context)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
        return salt + iv + ciphertext

    def decrypt(self, encrypted_data: bytes, context: str = "default") -> str:
        if not encrypted_data:
            return ""
        salt = encrypted_data[:16]
        iv = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]
        key = self._derive_key(salt, context)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext.decode("utf-8")


_encryption_service = None


def get_encryption_service() -> EncryptionService:
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(get_settings().MASTER_ENCRYPTION_KEY)
    return _encryption_service
