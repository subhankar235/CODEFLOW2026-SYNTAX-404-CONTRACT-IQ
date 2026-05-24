"""Rate limiting using Redis for upload and scan endpoints."""

import redis.asyncio as redis
from fastapi import HTTPException, status
from app.core.config import settings


class RateLimiter:
    """Redis-based rate limiter using sliding window."""

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def close(self):
        if self._redis:
            await self._redis.close()

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if request is within rate limit.
        Returns True if allowed, raises HTTPException if exceeded.
        """
        try:
            r = await self._get_redis()
            current = await r.incr(key)

            if current == 1:
                await r.expire(key, window_seconds)

            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window_seconds // 60} minutes.",
                )

            return True
        except HTTPException:
            raise
        except Exception as e:
            # If Redis fails, allow the request (fail open)
            # In production, you might want to log this
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_upload_limit(user_id: str) -> bool:
    """Check if user has exceeded upload rate limit (10 uploads/hour)."""
    key = f"rate_limit:upload:{user_id}"
    return await rate_limiter.check_rate_limit(key, limit=10, window_seconds=3600)


async def check_scan_limit(user_id: str) -> bool:
    """Check if user has exceeded scan rate limit (10 scans/hour)."""
    key = f"rate_limit:scan:{user_id}"
    return await rate_limiter.check_rate_limit(key, limit=10, window_seconds=3600)
