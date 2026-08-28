"""Integration test for the two-step login flow, against the real configured
database (whatever DATABASE_URL points to — inside the backend container,
that's the dev Postgres). Skips itself if the DB or the seeded 'admin' user
isn't reachable, rather than failing a run that simply has no DB available.

Run inside the backend container, after seed_demo.py has been run at least once:
    docker exec inspection-backend pip install -r requirements-dev.txt
    docker exec inspection-backend pytest tests/ -v
"""
import pyotp
import pytest
import httpx
from sqlalchemy import select

from app.main import app
from app.db.session import async_session_maker
from app.models import User
from app.core.encryption import get_encryption_service


async def _get_admin_totp_secret():
    enc = get_encryption_service()
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if not user:
            return None
        return enc.decrypt(user.totp_secret, context="totp_secret")


@pytest.fixture
async def totp_secret():
    try:
        secret = await _get_admin_totp_secret()
    except Exception as e:
        pytest.skip(f"Database not reachable for integration test: {e}")
    if not secret:
        pytest.skip("Seeded 'admin' user not found — run seed_demo.py first")
    return secret


async def test_full_login_flow_issues_tokens(totp_secret):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        temp_token = resp.json()["temp_token"]

        code = pyotp.TOTP(totp_secret).now()
        resp = await client.post("/api/v1/auth/verify-totp", json={"temp_token": temp_token, "totp_code": code})
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["user"]["username"] == "admin"


async def test_wrong_password_is_rejected():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "definitely-wrong"})
        assert resp.status_code == 401


async def test_protected_endpoint_rejects_missing_token():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/dashboard/stats")
        assert resp.status_code == 401
