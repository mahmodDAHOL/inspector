"""Shared pytest fixtures.

Provides fallback SECRET_KEY/MASTER_ENCRYPTION_KEY so the unit tests (which
don't touch the database) can import the app's modules without needing a full
.env — config.py now refuses to start with missing/weak secrets, which is the
correct behavior for the real app, so tests supply their own throwaway ones.
Real deployments must never use these values.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-never-use-in-production")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", "dGVzdC1vbmx5LW1hc3Rlci1rZXktbmV2ZXItcHJvZC0=")

import pytest


@pytest.fixture(autouse=True)
async def _reset_async_clients_between_tests():
    """pytest-asyncio gives each test its own event loop; a cached async Redis
    client or SQLAlchemy engine/connection-pool from a previous test's loop
    errors on reuse in the next one. Dispose/reset both per test — this only
    matters for tests: a real server has exactly one long-lived event loop
    per worker process, so nothing here reflects a production concern."""
    from app.core import rate_limit
    from app.db import session as db_session

    rate_limit._redis_client = None
    yield
    rate_limit._redis_client = None
    await db_session.engine.dispose()
