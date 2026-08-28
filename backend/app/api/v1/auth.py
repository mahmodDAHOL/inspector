"""Authentication API Routes"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_token,
    verify_totp,
)
from app.core.encryption import get_encryption_service
from app.core.activity_log import log_activity
from app.core.rate_limit import rate_limit

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


class LoginRequest(BaseModel):
    username: str
    password: str


class TOTPVerifyRequest(BaseModel):
    temp_token: str
    totp_code: str


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

    temp_token = create_temp_token({"sub": str(user.id)})
    return {"temp_token": temp_token, "requires_mfa": True}


@router.post("/verify-totp", dependencies=[mfa_rate_limit])
async def verify_totp(request: TOTPVerifyRequest, db: AsyncSession = Depends(get_db)):
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
    await db.commit()

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "full_name_ar": user.full_name_ar,
            "full_name_en": user.full_name_en,
            "role": user.role,
        },
    }


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
