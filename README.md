# Inspection Portal
## بوابة الرقابة والتفتيش — وزارة الإعلام

### Quick Start (Docker)

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your passwords

# 2. Create SSL certificates
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout ssl/inspection-portal.key \
  -out ssl/inspection-portal.crt \
  -subj "/C=SY/O=Ministry of Information/CN=localhost"

# 3. Build and run
docker compose build
docker compose up -d db redis
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/create_admin.py
docker compose up -d

# 4. Open browser
# https://localhost
```

### Structure
- `backend/` — FastAPI application
- `frontend/` — Vue.js 3 application
- `nginx/` — Reverse proxy configuration
- `ssl/` — SSL certificates
- `init-scripts/` — Database initialization
- `docs/` — Documentation
