"""Inspection Portal Backend — FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import auth, complaints, external, users, audit, reports, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Inspection Portal API",
    description="مديرية الرقابة والتفتيش — وزارة الإعلام",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if False else None,
    redoc_url="/api/redoc" if False else None,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=600,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api/v1/complaints", tags=["Complaints"])
app.include_router(external.router, prefix="/api/v1/external", tags=["External"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/v1/health")
async def api_health_check():
    return {"status": "healthy", "version": "1.0.0"}
