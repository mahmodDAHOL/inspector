"""Redis-backed IP rate limiting for sensitive/public endpoints.

Fails OPEN if Redis is unreachable — a rate limiter that can itself take the
whole API down when its backing store hiccups would trade one availability
problem for a worse one. This is a defense-in-depth layer on top of, not a
replacement for, the per-account lockout in auth.py.
"""
import logging

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _redis_client


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    """Dependency factory: at most `max_requests` per `window_seconds` per client IP."""

    async def _check(request: Request):
        ip = _client_ip(request)
        key = f"ratelimit:{key_prefix}:{ip}"
        try:
            client = _get_redis()
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, window_seconds)
            if count > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests, please try again later",
                )
        except HTTPException:
            raise
        except Exception:
            logger.warning("Rate limiter unavailable (Redis) — allowing request through", exc_info=True)

    return _check
