#!/usr/bin/env python3
"""Seed demo data for local development"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

import pyotp
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models import User, Complaint, Department
from app.models.base import Base
from app.core.security import get_password_hash
from app.core.encryption import get_encryption_service
from app.core.config import get_settings

enc = get_encryption_service()
settings = get_settings()

DEMO_USERS = [
    {
        "id": uuid4(),
        "username": "admin",
        "password": "admin123",
        "full_name_ar": "مدير النظام",
        "full_name_en": "System Administrator",
        "email": "admin@mediagate.gov.sy",
        "phone": "+963991234567",
        "role": "super_admin",
    },
    {
        "id": uuid4(),
        "username": "inspector",
        "password": "inspector123",
        "full_name_ar": "أحمد خالد",
        "full_name_en": "Ahmed Khaled",
        "email": "ahmed@mediagate.gov.sy",
        "phone": "+963992345678",
        "role": "senior_inspector",
    },
    {
        "id": uuid4(),
        "username": "junior",
        "password": "junior123",
        "full_name_ar": "خالد عمر",
        "full_name_en": "Khaled Omar",
        "email": "khaled@mediagate.gov.sy",
        "phone": "+963993456789",
        "role": "inspector",
    },
]

DEPARTMENT_ID = uuid4()

COMPLAINT_TITLES = [
    ("مخالفة في إجراءات التعاقد", "Procurement Violation"),
    ("إهدار مالي في مشروع عام", "Financial Fraud"),
    ("تأخير في تسليم تقرير التفتيش", "Delay in Inspection Report"),
    ("تجاوزات في صرف المكافآت", "Irregular Bonus Payments"),
    ("استخدام مركبات الدولة لأغراض شخصية", "Misuse of Government Vehicles"),
    ("تلاعب في نتائج المناقصة", "Bid Rigging"),
    ("غياب متكرر دون عذر", "Unauthorized Absences"),
    ("تسريب معلومات سرية", "Leak of Confidential Information"),
    ("مخالفات في إدارة المخزون", "Inventory Mismanagement"),
    ("صرف دون مستندات رسمية", "Unauthorized Spending"),
    ("تعيين بدون مسابقة", "Irregular Hiring"),
    ("رشوة مقابل تسهيلات إدارية", "Bribery for Administrative Favors"),
    ("تجاوز صلاحيات الموظف", "Employee Authority Abuse"),
    ("إخفاء تقارير سلبية", "Concealment of Negative Reports"),
    ("تزوير في الوثائق الرسمية", "Document Forgery"),
]

STATUS_FLOW = ["received", "under_investigation", "closed"]
PRIORITIES = ["normal", "urgent", "critical"]


def encrypt_field(value: str, context: str) -> bytes:
    return enc.encrypt(value or "", context=context)


def generate_complaint_number(index: int) -> str:
    return f"INS-{datetime.utcnow().year}-{index + 1:04d}"


async def seed():
    async with async_session_maker() as session:
        await clear_existing(session)
        await create_department(session)
        await session.flush()
        users = await create_users(session)
        await session.flush()
        await create_complaints(session, users)
        await session.commit()
        print("\n✅ Demo data seeded successfully.\n")
        print("Login credentials:")
        for u in DEMO_USERS:
            totp = pyotp.TOTP(users[u["username"]]["totp_secret"])
            print(f"  {u['username']:12s} / {u['password']:15s}  TOTP: {totp.now()}")
        print("\nTOTP codes refresh every 30 seconds. Re-run this script to get current codes.")


async def clear_existing(session: AsyncSession):
    for table in ["digital_signatures", "investigation_notes", "complaint_logs", "activity_logs", "complaints", "users", "departments"]:
        await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
    await session.commit()
    print("Cleared existing demo data.")


async def create_department(session: AsyncSession):
    dept = Department(
        id=DEPARTMENT_ID,
        name_ar="مديرية الرقابة والتفتيش",
        name_en="Inspection Directorate",
        code="INSP",
    )
    session.add(dept)
    print("Created demo department.")


async def create_users(session: AsyncSession):
    created = {}
    for data in DEMO_USERS:
        totp_secret = pyotp.random_base32()
        user = User(
            id=data["id"],
            username=data["username"],
            password_hash=get_password_hash(data["password"]),
            full_name_ar=data["full_name_ar"],
            full_name_en=data["full_name_en"],
            email=encrypt_field(data["email"], "email"),
            phone=encrypt_field(data["phone"], "phone"),
            role=data["role"],
            department_id=DEPARTMENT_ID,
            totp_secret=encrypt_field(totp_secret, "totp_secret"),
            is_active=True,
        )
        session.add(user)
        created[data["username"]] = {"user": user, "totp_secret": totp_secret}
    return created


async def create_complaints(session: AsyncSession, users: dict):
    admin_user = users["admin"]["user"]
    inspector_user = users["inspector"]["user"]
    junior_user = users["junior"]["user"]

    for i, (title_ar, title_en) in enumerate(COMPLAINT_TITLES):
        status = STATUS_FLOW[i % 3]
        priority = PRIORITIES[i % 3]
        assigned = [inspector_user.id, junior_user.id, None][i % 3]
        created_by = admin_user.id if i % 2 == 0 else inspector_user.id
        created_at = datetime.utcnow() - timedelta(days=i + 2)
        closed_at = datetime.utcnow() - timedelta(days=i) if status == "closed" else None
        # Complaints past "received" have already gotten a first response; vary the delay
        # so the response-time SLA metrics on the dashboard show realistic numbers.
        first_response_at = created_at + timedelta(hours=4 + (i % 5) * 6) if status != "received" else None

        complaint = Complaint(
            id=uuid4(),
            complaint_number=generate_complaint_number(i),
            title_ar=title_ar,
            title_en=title_en,
            description=encrypt_field(
                f"تفاصيل الشكوى رقم {i + 1} - تحقيق مطلوب في المخالفات المبلغ عنها.",
                "description",
            ),
            source="Direct",
            category=["procurement_violation", "financial_fraud", "bribery", "misconduct"][i % 4],
            priority=priority,
            status=status,
            assigned_to=assigned,
            created_by=created_by,
            erp_reference_id=f"ERP-{datetime.utcnow().year}-{1000 + i}",
            is_anonymous=False,
            created_at=created_at,
            updated_at=datetime.utcnow() - timedelta(days=i),
            closed_at=closed_at,
            first_response_at=first_response_at,
        )
        session.add(complaint)
    print(f"Created {len(COMPLAINT_TITLES)} demo complaints.")


if __name__ == "__main__":
    asyncio.run(seed())
