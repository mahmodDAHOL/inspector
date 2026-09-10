"""Authentication API Routes"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User, TrustedDevice
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_token,
    verify_totp,
    generate_device_secret,
    hash_device_token,
    verify_device_token,
)
from app.core.encryption import get_encryption_service
from app.core.activity_log import log_activity
from app.core.rate_limit import rate_limit
from app.core.deps import get_current_user

router = APIRouter()

# Independent of the per-account lockout below — this caps how many login/MFA
# attempts a single IP can make regardless of which usernames it targets, so a
# credential-spraying attacker can't dodge the per-account lockout by trying
# many different accounts a few times each.
login_rate_limit = Depends(rate_limit("auth-login", max_requests=15, window_seconds=60))
mfa_rate_limit = Depends(rate_limit("auth-mfa", max_requests=15, window_seconds=60))
enc = get_encryption_service()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
TRUSTED_DEVICE_DAYS = 30


class LoginRequest(BaseModel):
    username: str
    password: str
    # Optional: a device previously trusted via `remember_device` on /verify-totp.
    # Both must be present and valid to skip the TOTP step — the password
    # check above still always runs first and still always runs in full.
    device_id: Optional[str] = None
    device_token: Optional[str] = None


class TOTPVerifyRequest(BaseModel):
    temp_token: str
    totp_code: str
    remember_device: bool = False
    device_label: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", dependencies=[login_rate_limit])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Step 1: Login with credentials"""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user:
        await log_activity(db, "auth", "login_failed", f"Failed login attempt for unknown username '{request.username}'")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        await log_activity(db, "auth", "login_failed", "Login attempt on a disabled account", performed_by=user.id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    if user.locked_until and user.locked_until > datetime.utcnow():
        await log_activity(db, "auth", "login_failed", "Login attempt on a locked account", performed_by=user.id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until.isoformat()}Z due to repeated failed logins",
        )

    if not verify_password(request.password, user.password_hash):
        attempts = int(user.failed_login_attempts or "0") + 1
        user.failed_login_attempts = str(attempts)
        if attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            await log_activity(db, "auth", "account_locked", f"Account locked for {LOCKOUT_MINUTES} minutes after {attempts} failed attempts", performed_by=user.id)
        else:
            await log_activity(db, "auth", "login_failed", f"Wrong password (attempt {attempts}/{MAX_FAILED_ATTEMPTS})", performed_by=user.id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.failed_login_attempts = "0"
    user.locked_until = None
    await db.commit()

    # Password is correct. If the client also presented a still-valid trusted
    # device, skip straight to issuing tokens — the TOTP step is the only
    # thing this ever bypasses, never the password check above.
    if request.device_id and request.device_token:
        device = await _find_valid_device(db, user.id, request.device_id)
        if device and verify_device_token(request.device_token, device.token_hash):
            new_secret = generate_device_secret()
            device.token_hash = hash_device_token(new_secret)
            device.last_used_at = datetime.utcnow()
            device.expires_at = datetime.utcnow() + timedelta(days=TRUSTED_DEVICE_DAYS)

            user.last_login_at = datetime.utcnow()
            await log_activity(db, "auth", "login_success", f"{user.username} logged in via trusted device", performed_by=user.id)
            await db.commit()

            return {
                **_issue_tokens(user),
                "requires_mfa": False,
                "device_id": str(device.device_id),
                "device_token": new_secret,
            }
        else:
            await log_activity(db, "auth", "device_rejected", "Presented device_id/device_token did not match a valid trusted device", performed_by=user.id)
            await db.commit()

    temp_token = create_temp_token({"sub": str(user.id)})
    return {"temp_token": temp_token, "requires_mfa": True}


async def _find_valid_device(db: AsyncSession, user_id, device_id: str) -> Optional[TrustedDevice]:
    try:
        device_uuid = uuid.UUID(device_id)
    except (ValueError, AttributeError, TypeError):
        return None
    result = await db.execute(
        select(TrustedDevice).where(
            TrustedDevice.device_id == device_uuid,
            TrustedDevice.user_id == user_id,
            TrustedDevice.revoked.is_(False),
        )
    )
    device = result.scalar_one_or_none()
    if not device or device.expires_at < datetime.utcnow():
        return None
    return device


def _issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id), "role": user.role}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name_ar": user.full_name_ar,
            "full_name_en": user.full_name_en,
            "role": user.role,
        },
    }


@router.post("/verify-totp", dependencies=[mfa_rate_limit])
async def verify_totp_step(request: TOTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Step 2: Verify TOTP code and issue tokens"""
    try:
        payload = decode_token(request.temp_token)
        if payload.get("type") != "temp":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired temp token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    totp_secret = enc.decrypt(user.totp_secret, context="totp_secret")
    if not verify_totp(totp_secret, request.totp_code):
        await log_activity(db, "auth", "mfa_failed", "Invalid MFA code entered", performed_by=user.id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    user.last_login_at = datetime.utcnow()
    await log_activity(db, "auth", "login_success", f"{user.username} logged in", performed_by=user.id)

    response = _issue_tokens(user)

    if request.remember_device:
        secret = generate_device_secret()
        trusted = TrustedDevice(
            user_id=user.id,
            device_id=uuid.uuid4(),
            token_hash=hash_device_token(secret),
            label=(request.device_label or "")[:100] or None,
            expires_at=datetime.utcnow() + timedelta(days=TRUSTED_DEVICE_DAYS),
        )
        db.add(trusted)
        await log_activity(db, "auth", "device_trusted", f"New trusted device registered for {user.username}", performed_by=user.id)
        response["device_id"] = str(trusted.device_id)
        response["device_token"] = secret

    await db.commit()
    return response


class RevokeDeviceRequest(BaseModel):
    device_id: str


@router.post("/revoke-device")
async def revoke_device(
    request: RevokeDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Un-trust a device — e.g. the user tapped 'forget this device', or lost the phone."""
    device = await _find_valid_device(db, current_user.id, request.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching active trusted device")
    device.revoked = True
    await log_activity(db, "auth", "device_revoked", f"Trusted device revoked by {current_user.username}", performed_by=current_user.id)
    await db.commit()
    return {"message": "Device revoked"}


@router.post("/refresh")
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token — takes the refresh token as a JSON body, never a query string"""
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Re-read the role from the DB rather than trusting a stale claim
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}
