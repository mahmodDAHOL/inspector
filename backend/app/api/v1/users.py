"""Users API Routes (Admin Only)"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User, Department
from app.core.security import get_password_hash, generate_totp_secret, validate_password_strength
from app.core.encryption import get_encryption_service
from app.core.deps import get_current_user, require_roles
from app.core.activity_log import log_activity

router = APIRouter(dependencies=[Depends(get_current_user)])
enc = get_encryption_service()

ROLES = ["super_admin", "admin", "senior_inspector", "inspector", "viewer"]


class UserCreate(BaseModel):
    username: str
    full_name_ar: str
    full_name_en: str
    email: str
    role: str
    password: str
    department_id: Optional[UUID4] = None

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    full_name_ar: Optional[str] = None
    full_name_en: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[UUID4] = None


class UserResponse(BaseModel):
    id: UUID4
    username: str
    full_name_ar: str
    full_name_en: str
    email: Optional[str]
    role: str
    is_active: bool
    department_id: Optional[UUID4]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class UserCreatedResponse(UserResponse):
    totp_secret: str


@router.get("/roles")
async def list_roles():
    """List available user roles"""
    return {"roles": ROLES}


@router.get("", response_model=List[UserResponse])
async def list_users(limit: int = 200, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """List users, capped and paginated (default page size 200)"""
    query = select(User).order_by(User.created_at.desc()).offset(max(offset, 0)).limit(min(max(limit, 1), 500))
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name_ar": u.full_name_ar,
            "full_name_en": u.full_name_en,
            "email": enc.decrypt(u.email, context="email") or None,
            "role": u.role,
            "is_active": u.is_active,
            "department_id": u.department_id,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID4, db: AsyncSession = Depends(get_db)):
    """Get user details"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "full_name_ar": user.full_name_ar,
        "full_name_en": user.full_name_en,
        "email": enc.decrypt(user.email, context="email") or None,
        "role": user.role,
        "is_active": user.is_active,
        "department_id": user.department_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("", response_model=UserCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("super_admin")),
):
    """Create new user (superuser only)"""
    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    department_id = user.department_id
    if not department_id:
        dept_result = await db.execute(select(Department.id).limit(1))
        department_row = dept_result.fetchone()
        department_id = department_row[0] if department_row else None

    totp_secret = generate_totp_secret()
    new_user = User(
        username=user.username,
        password_hash=get_password_hash(user.password),
        full_name_ar=user.full_name_ar,
        full_name_en=user.full_name_en,
        email=enc.encrypt(user.email, context="email"),
        phone=enc.encrypt("", context="phone"),
        role=user.role,
        department_id=department_id,
        totp_secret=enc.encrypt(totp_secret, context="totp_secret"),
    )
    db.add(new_user)
    await db.flush()
    await log_activity(db, "user", "user_created", f"User '{new_user.username}' created with role {new_user.role}", performed_by=_admin.id, entity_id=new_user.id)
    await db.commit()
    await db.refresh(new_user)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "full_name_ar": new_user.full_name_ar,
        "full_name_en": new_user.full_name_en,
        "email": enc.decrypt(new_user.email, context="email") or None,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "department_id": new_user.department_id,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
        "totp_secret": totp_secret,
    }


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID4,
    update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin", "super_admin")),
):
    """Update user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_role = user.role
    old_active = user.is_active

    if update.full_name_ar is not None:
        user.full_name_ar = update.full_name_ar
    if update.full_name_en is not None:
        user.full_name_en = update.full_name_en
    if update.email is not None:
        user.email = enc.encrypt(update.email, context="email")
    if update.role is not None:
        user.role = update.role
    if update.is_active is not None:
        user.is_active = update.is_active
    if update.department_id is not None:
        user.department_id = update.department_id

    changes = []
    if update.role is not None and update.role != old_role:
        changes.append(f"role {old_role} -> {update.role}")
    if update.is_active is not None and update.is_active != old_active:
        changes.append("activated" if update.is_active else "deactivated")
    description = f"User '{user.username}' updated ({', '.join(changes)})" if changes else f"User '{user.username}' profile updated"
    await log_activity(db, "user", "user_updated", description, performed_by=_admin.id, entity_id=user.id)

    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "full_name_ar": user.full_name_ar,
        "full_name_en": user.full_name_en,
        "email": enc.decrypt(user.email, context="email") or None,
        "role": user.role,
        "is_active": user.is_active,
        "department_id": user.department_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID4,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin", "super_admin")),
):
    """Deactivate user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await log_activity(db, "user", "user_deactivated", f"User '{user.username}' deactivated", performed_by=_admin.id, entity_id=user.id)
    await db.commit()
    return {"message": "User deactivated", "user_id": str(user_id)}
