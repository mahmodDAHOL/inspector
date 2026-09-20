"""Inspection Portal Backend — FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import auth, complaints, external, users, audit, reports, dashboard, departments, minutes, investigation_reports, evidence
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Inspection Portal API",
    description="مديرية الرقابة والتفتيش — وزارة الإعلام",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts_list,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    # The app authenticates with a Bearer token (Authorization header / JSON body),
    # never cookies, so it has no use for CORS "credentials" mode - and turning it
    # off is what makes it safe to list "*" in ALLOWED_ORIGINS when that's needed
    # (e.g. calling the API from a page whose exact origin isn't known in advance,
    # such as a hosted demo/tunnel). allow_origins=["*"] + allow_credentials=True
    # is the dangerous combination; this app never pairs the two.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
app.include_router(minutes.router, prefix="/api/v1/complaints", tags=["Minutes"])
app.include_router(external.router, prefix="/api/v1/external", tags=["External"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(departments.router, prefix="/api/v1/departments", tags=["Departments"])
app.include_router(investigation_reports.router, prefix="/api/v1/complaints", tags=["Investigation Reports"])
app.include_router(evidence.router, prefix="/api/v1/complaints", tags=["Evidence"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/v1/health")
async def api_health_check():
    return {"status": "healthy", "version": "1.0.0"}
