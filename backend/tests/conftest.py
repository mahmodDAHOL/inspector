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
