"""Users API Routes (Admin Only)"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    full_name_ar: str
    full_name_en: str
    email: str
    role: str


@router.get("")
async def list_users():
    """List all users (Admin only)"""
    return [
        {"id": "user-1", "username": "admin", "full_name_ar": "مدير النظام", "role": "super_admin"},
        {"id": "user-2", "username": "inspector_ahmed", "full_name_ar": "أحمد خالد", "role": "senior_inspector"}
    ]


@router.post("")
async def create_user(user: UserCreate):
    """Create new user"""
    return {"id": "new-user-uuid", "username": user.username, "message": "User created"}
