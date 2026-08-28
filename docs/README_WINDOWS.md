# دليل التشغيل على Windows (للتجريب المحلي)
# Windows Local Development Guide — Inspection Portal

---

## المتطلبات

| البرنامج | الإصدار الأدنى | الرابط |
|----------|---------------|--------|
| Python | 3.12 | https://python.org/downloads |
| Node.js | 20 | https://nodejs.org |
| Git | 2.40 | https://git-scm.com |
| VS Code (مستحسن) | - | https://code.visualstudio.com |

> **ملاحظة:** تأكد من إضافة Python و Node.js إلى متغير PATH أثناء التثبيت.

---

## الخطوة ١: تحميل المشروع

```powershell
# فتح PowerShell كمسؤول (Admin)
# إنشاء مجلد المشروع
mkdir C:\Projects\inspection-portal
cd C:\Projects\inspection-portal

# استنساخ المستودع (أو نسخ الملفات يدوياً)
git clone <repository-url> .
```

---

## الخطوة ٢: إعداد Backend (Python)

### ٢.١ إنشاء بيئة افتراضية

```powershell
cd C:\Projects\inspection-portalackend

# إنشاء البيئة الافتراضية
python -m venv venv

# تفعيل البيئة
.\venv\Scripts\activate

# ستظهر (venv) قبل اسم المجلد في PowerShell
```

### ٢.٢ تثبيت التبعيات

```powershell
# تأكد من أنك داخل البيئة الافتراضية
pip install --upgrade pip
pip install -r requirements.txt

# للتجريب المحلي بدون PostgreSQL (SQLite)
pip install aiosqlite
```

### ٢.٣ إعداد ملف البيئة

```powershell
# نسخ ملف البيئة
Copy-Item .env.example .env

# فتح الملف في VS Code لتعديله
 code .env
```

محتوى `.env` للتجريب المحلي:
```env
APP_NAME=Inspection Portal
APP_VERSION=1.0.0
DEBUG=true

# Security (استخدم هذه القيم للتجريب فقط)
SECRET_KEY=dev-secret-key-change-in-production-64-characters-long
MASTER_ENCRYPTION_KEY=bW9ja19lbmNyeXB0aW9uX2tleV8xMjM0NTY=

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
TOTP_ISSUER=Syria-MOI-Inspection-Dev

# Database (SQLite للتجريب المحلي)
DATABASE_URL=sqlite+aiosqlite:///./inspection_portal_dev.db
DB_POOL_SIZE=10

# Redis (للتجريب بدون Redis)
REDIS_URL=memory://

# MediaGate (وضع وهمي للتجريب)
MEDIAGATE_API_URL=http://localhost:9999
MEDIAGATE_API_KEY=dev-key
MEDIAGATE_POLL_INTERVAL_MINUTES=5

# File Storage
UPLOAD_DIR=.\uploads
MAX_FILE_SIZE_MB=50

# Audit
AUDIT_LOG_RETENTION_YEARS=7
```

### ٢.٤ إنشاء قاعدة البيانات

```powershell
# تشغيل سكريبت التهيئة
python scripts\init_db.py

# أو يدوياً:
python -c "from app.main import init_db; import asyncio; asyncio.run(init_db())"
```

### ٢.٥ إنشاء مستخدم Admin أولي

```powershell
python scripts\create_admin.py
```

سيطلب منك:
- اسم المستخدم: `admin`
- كلمة المرور: (أدخل كلمة قوية)
- الاسم الكامل: `مدير النظام`

### ٢.٦ تشغيل الخادم

```powershell
# الوضع التلقائي (مع إعادة التحميل)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# أو باستخدام PowerShell سكريبت
.\run.ps1
```

افتح المتصفح وانتقل إلى: `http://localhost:8000/docs`
سترى وثائق API التفاعلية (Swagger UI).

---

## الخطوة ٣: إعداد Frontend (Vue.js)

### ٣.١ تثبيت التبعيات

```powershell
cd C:\Projects\inspection-portalrontend

# تثبيت التبعيات
npm install

# إذا واجهت مشاكل في npm:
npm install --legacy-peer-deps
```

### ٣.٢ إعداد ملف البيئة

```powershell
# إنشاء ملف .env.local
@"
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Inspection Portal
"@ | Out-File -FilePath .env.local -Encoding utf8
```

### ٣.٣ تشغيل خادم التطوير

```powershell
npm run dev
```

افتح المتصفح وانتقل إلى: `http://localhost:5173`

---

## الخطوة ٤: تشغيل كامل (Backend + Frontend)

### الطريقة السريعة (سكريبت PowerShell)

```powershell
# من مجلد المشروع الرئيسي
.\start-dev.ps1
```

هذا السكريبت يشغل:
1. Backend على `http://localhost:8000`
2. Frontend على `http://localhost:5173`
3. يفتح المتصفح تلقائياً

---

## بيانات تجريبية (Demo Data)

### إضافة بيانات وهمية

```powershell
cd C:\Projects\inspection-portalackend
.\venv\Scripts\activate

python scripts\seed_demo_data.py
```

هذا يضيف:
- 5 مستخدمين (مفتشين)
- 20 شكوى بأنواع مختلفة
- ملاحظات تحقيق
- مرفقات وهمية

### بيانات الدخول الافتراضية

| اسم المستخدم | كلمة المرور | الدور |
|-------------|------------|-------|
| admin | Admin@123 | مدير النظام |
| inspector_ahmed | Pass@123 | مفتش |
| inspector_layla | Pass@123 | مفتشة |
| director_khaled | Pass@123 | مدير الرقابة |

---

## استكشاف الأخطاء الشائعة

### الخطأ: "ModuleNotFoundError"

```powershell
# الحل: تأكد من تفعيل البيئة الافتراضية
.\venv\Scripts\activate

# ثم أعد تثبيت التبعيات
pip install -r requirements.txt
```

### الخطأ: "Port 8000 is already in use"

```powershell
# إيجاد العملية التي تستخدم المنفذ
netstat -ano | findstr :8000

# إنهاؤها (استبدل PID بالرقم)
taskkill /PID 12345 /F

# أو تشغيل الخادم على منفذ آخر
uvicorn app.main:app --port 8001
```

### الخطأ: "npm install fails"

```powershell
# تنظيف ذاكرة التخزين
npm cache clean --force

# حذف node_modules وإعادة التثبيت
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### الخطأ: "CORS policy"

```powershell
# تأكد من أن Frontend يتصل بالـ API الصحيح
# في ملف .env.local:
VITE_API_URL=http://localhost:8000/api/v1
```

### الخطأ: "SQLite database is locked"

```powershell
# SQLite لا يدعم الكتابة المتزامنة جيداً
# أغلق أي برنامج يفتح ملف .db
# أو استخدم PostgreSQL للتطوير الجدي
```

---

## هيكل المجلدات (Windows)

```
C:\Projects\inspection-portal├── backend│   ├── app│   │   ├── api│   │   ├── core│   │   ├── models│   │   └── main.py
│   ├── scripts│   │   ├── init_db.py
│   │   ├── create_admin.py
│   │   └── seed_demo_data.py
│   ├── uploads│   ├── venv│   ├── requirements.txt
│   └── .env
├── frontend│   ├── src│   │   ├── views│   │   ├── components│   │   ├── stores│   │   └── api│   ├── public│   ├── node_modules│   ├── package.json
│   └── .env.local
├── inspection_portal_dev.db  (SQLite)
├── start-dev.ps1
└── README_WINDOWS.md
```

---

## التبديل إلى PostgreSQL (للتطوير المتقدم)

إذا أردت استخدام PostgreSQL بدلاً من SQLite:

### ١. تثبيت PostgreSQL

```powershell
# تحميل PostgreSQL 16
# https://www.postgresql.org/download/windows/

# أو باستخدام Chocolatey
choco install postgresql16
```

### ٢. إنشاء قاعدة البيانات

```powershell
# فتح psql
& "C:\Program Files\PostgreSQLin\psql.exe" -U postgres

# داخل psql:
CREATE DATABASE inspection_portal_dev;
CREATE USER inspection_dev WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE inspection_portal_dev TO inspection_dev;
\q
```

### ٣. تحديث .env

```env
DATABASE_URL=postgresql+asyncpg://inspection_dev:dev_password@localhost:5432/inspection_portal_dev
```

### ٤. إعادة تهيئة

```powershell
pip install asyncpg
python scripts\init_db.py
```

---

## إيقاف التشغيل

```powershell
# إيقاف Backend
# اضغط Ctrl+C في نافذة PowerShell

# إيقاف Frontend
# اضغط Ctrl+C في نافذة PowerSL

# أو استخدم السكريبت
.\stop-dev.ps1
```

---

## التالي

بعد التأكد من عمل المشروع محلياً:

1. اقرأ `deployment_guide.md` للنشر الإنتاجي
2. اقرأ `security_test_plan.md` لاختبار الأمان
3. راجع `technical_specification.md` للتفاصيل الكاملة

---

**Document Version: 1.0**
**Date: 2026-08-28**
**© الجمهورية العربية السورية — وزارة الإعلام**
