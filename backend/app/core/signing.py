"""Digital signature service — real RSA-PSS/SHA-384 signatures for signed reports.

The system keypair is generated once and persisted to disk (under UPLOAD_DIR,
which is a durable Docker volume) so every signature can be verified against
the same public key for the life of the deployment.
"""
import base64
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.core.config import get_settings

_ALGORITHM = "RSA-PSS-SHA384"
_cached_key = None


def _key_path() -> Path:
    base = Path(get_settings().UPLOAD_DIR) / "system"
    base.mkdir(parents=True, exist_ok=True)
    return base / "signing_key.pem"


def _get_or_create_private_key() -> rsa.RSAPrivateKey:
    global _cached_key
    if _cached_key is not None:
        return _cached_key

    path = _key_path()
    if path.exists():
        with open(path, "rb") as f:
            _cached_key = serialization.load_pem_private_key(f.read(), password=None)
        return _cached_key

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(pem)
    _cached_key = key
    return key


def certificate_thumbprint() -> str:
    """SHA-256 thumbprint of the system's public key (stable identity for verifiers)."""
    key = _get_or_create_private_key()
    public_der = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(public_der).hexdigest()


def sign_payload(payload: str) -> dict:
    """Sign a canonical string payload. Returns the signature (base64), algorithm, and thumbprint."""
    key = _get_or_create_private_key()
    signature = key.sign(
        payload.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA384(),
    )
    return {
        "signature": base64.b64encode(signature).decode("ascii"),
        "algorithm": _ALGORITHM,
        "certificate_thumbprint": certificate_thumbprint(),
    }


def verify_payload(payload: str, signature_b64: str) -> bool:
    """Verify a previously-produced signature against the current system public key."""
    key = _get_or_create_private_key()
    try:
        key.public_key().verify(
            base64.b64decode(signature_b64),
            payload.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA384(),
        )
        return True
    except Exception:
        return False
