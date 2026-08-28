"""Departments API Routes"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Department, User
from app.core.deps import get_current_user, require_roles
from app.core.activity_log import log_activity

router = APIRouter()


class DepartmentCreate(BaseModel):
    name_ar: str
    name_en: Optional[str] = None
    code: str
    parent_id: Optional[UUID4] = None


class DepartmentUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[UUID4] = None


class DepartmentResponse(BaseModel):
    id: UUID4
    name_ar: str
    name_en: Optional[str]
    code: str
    parent_id: Optional[UUID4]
    created_at: Optional[str]

    class Config:
        from_attributes = True


def _serialize(d: Department) -> dict:
    return {
        "id": d.id,
        "name_ar": d.name_ar,
        "name_en": d.name_en,
        "code": d.code,
        "parent_id": d.parent_id,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    """List all departments"""
    result = await db.execute(select(Department).order_by(Department.name_en))
    return [_serialize(d) for d in result.scalars().all()]


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin", "super_admin")),
):
    """Create a new department (admin only)"""
    existing = await db.execute(select(Department).where(Department.code == department.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department code already exists")

    new_department = Department(**department.model_dump())
    db.add(new_department)
    await db.flush()
    await log_activity(db, "department", "department_created", f"Department '{new_department.name_en or new_department.name_ar}' ({new_department.code}) created", performed_by=_user.id, entity_id=new_department.id)
    await db.commit()
    await db.refresh(new_department)
    return _serialize(new_department)


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID4,
    update: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin", "super_admin")),
):
    """Update a department (admin only)"""
    result = await db.execute(select(Department).where(Department.id == department_id))
    department = result.scalar_one_or_none()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(department, field, value)

    await log_activity(db, "department", "department_updated", f"Department '{department.code}' updated", performed_by=_user.id, entity_id=department.id)
    await db.commit()
    await db.refresh(department)
    return _serialize(department)
