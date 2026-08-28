"""Authentication API Routes"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

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
async def login(request: LoginRequest):
    """Step 1: Login with credentials"""
    return {"temp_token": "temp_123", "requires_mfa": True}


@router.post("/verify-totp")
async def verify_totp(request: TOTPVerifyRequest):
    """Step 2: Verify TOTP code"""
    return {
        "access_token": "access_123",
        "refresh_token": "refresh_123",
        "token_type": "bearer",
        "user": {
            "id": "user-uuid",
            "username": "admin",
            "full_name_ar": "مدير النظام",
            "role": "super_admin"
        }
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    return {"access_token": "new_access_123", "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}
