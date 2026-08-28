# دليل التشغيل على Docker
# Docker Deployment Guide — Inspection Portal
# الجمهورية العربية السورية — وزارة الإعلام

---

## المتطلبات

| البرنامج | الإصدار | التحقق |
|----------|---------|--------|
| Docker Engine | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.40+ | `git --version` |

---

## هيكل المجلدات المطلوب

```
inspection-portal/
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py
│       ├── api/
│       ├── core/
│       ├── models/
│       └── services/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── views/
│       ├── components/
│       ├── stores/
│       └── api/
├── nginx/
│   └── nginx.conf
├── ssl/
│   ├── inspection-portal.crt
│   └── inspection-portal.key
└── init-scripts/
    └── 01-init.sql
```

---

## الخطوة ١: إعداد المجلدات

### على Linux/macOS

```bash
mkdir -p inspection-portal/{backend/app,frontend/src,nginx,ssl,init-scripts}
cd inspection-portal
```

### على Windows (PowerShell)

```powershell
$folders = @("backend/app", "frontend/src", "nginx", "ssl", "init-scripts")
foreach ($f in $folders) { New-Item -ItemType Directory -Path $f -Force }
```

---

## الخطوة ٢: إعداد ملف البيئة (.env)

```bash
cat > .env <<'EOF'
APP_NAME=Inspection Portal
APP_VERSION=1.0.0
DEBUG=false

SECRET_KEY=change-me-in-production-64-characters-long
MASTER_ENCRYPTION_KEY=change-me-in-production-32-bytes
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
TOTP_ISSUER=Syria-MOI-Inspection

DB_PASSWORD=YourStrongDBPassword123!
REDIS_PASSWORD=YourStrongRedisPassword456!

MEDIAGATE_API_URL=https://mediagate.gov.sy/api
MEDIAGATE_API_KEY=your_actual_api_key_here
MEDIAGATE_POLL_INTERVAL_MINUTES=5

UPLOAD_DIR=/var/inspection/uploads
MAX_FILE_SIZE_MB=50
AUDIT_LOG_RETENTION_YEARS=7
EOF
```

---

## الخطوة ٣: إنشاء شهادة SSL

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:4096   -keyout ssl/inspection-portal.key   -out ssl/inspection-portal.crt   -subj "/C=SY/O=Ministry of Information/CN=localhost"

chmod 600 ssl/inspection-portal.key
```

---

## الخطوة ٤: أول تشغيل

### ٤.١ بناء الصور

```bash
docker compose build
```

### ٤.٢ تشغيل قاعدة البيانات

```bash
docker compose up -d db redis
docker compose ps
```

### ٤.٣ تشغيل الترحيلات

```bash
docker compose run --rm backend alembic upgrade head
```

### ٤.٤ إنشاء مستخدم Admin

```bash
docker compose run --rm backend python scripts/create_admin.py
```

### ٤.٥ تشغيل كل الخدمات

```bash
docker compose up -d
```

---

## التحقق من التشغيل

```
https://localhost          ← Frontend
https://localhost/api/docs ← API Docs
https://localhost/health   ← Health Check
```

---

## الأوامر اليومية

| العملية | الأمر |
|---------|-------|
| أول تشغيل | `docker compose up -d` |
| إيقاف | `docker compose stop` |
| إعادة تشغيل | `docker compose restart` |
| سجلات | `docker compose logs -f` |
| تحديث | `docker compose up -d --build` |
| نسخ احتياطي | `docker compose exec db pg_dump ...` |
| دخول DB | `docker compose exec db psql -U inspection_app` |
| حذف كل شيء | `docker compose down -v` |

---

## استكشاف الأخطاء

### "port is already allocated"

```bash
sudo lsof -i :80
sudo systemctl stop apache2
sudo systemctl stop nginx
```

### قاعدة البيانات لا تبدأ

```bash
docker compose logs db
docker compose down -v
docker volume rm inspection-portal_postgres_data
docker compose up -d db
```

### Backend لا يتصل بـ DB

```bash
docker compose exec db pg_isready -U inspection_app
docker compose restart backend
```

---

**Document Version: 1.0**
**Date: 2026-08-28**
**© الجمهورية العربية السورية — وزارة الإعلام**
