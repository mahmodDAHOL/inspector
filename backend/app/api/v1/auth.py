"""Authentication API Routes"""
from datetime import datetime
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

router = APIRouter()
enc = get_encryption_service()


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


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Step 1: Login with credentials"""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    temp_token = create_temp_token({"sub": str(user.id)})
    return {"temp_token": temp_token, "requires_mfa": True}


@router.post("/verify-totp")
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    user.last_login_at = datetime.utcnow()
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
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token({"sub": payload.get("sub"), "role": payload.get("role")})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}
