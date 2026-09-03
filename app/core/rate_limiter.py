import logging
import time

import redis.asyncio as aioredis

from app.core.config import settings


logger = logging.getLogger(__name__)


_rate_limiter: "RateLimiter | None" = None


class RateLimiter:
    """
    Distributed rate limiter using Redis sorted sets (sliding window).

    Algorithm:
    1. Clean entries older than the window
    2. Count remaining entries
    3. If count < limit → add current request, return True
    4. If count >= limit → return False (nothing added)
    """
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def connect(self):
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
            )

    async def acquire(
        self, 
        key: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """
        Try to acquire a rate limit slot.

        Args:
            key:             Redis key for this rate limit bucket
                             (e.g. "rate_limit:email").
            limit:           Max number of requests allowed in the window.
            window_seconds:  Window duration in seconds (e.g. 60 for per-minute).

        Returns:
            True  — slot acquired, proceed with the request.
            False — rate limit exceeded, caller should retry later.
        """

        if self._redis is None:
            await self.connect()

        now = time.time()
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()

        count = results[1]

        if count >= limit:
            logger.debug(
                "Rate limit exceeded (key=%s, count=%s, limit=%s)",
                key, count, limit,
            )
            return False

        request_id = f"{now}:{time.monotonic_ns()}"

        pipe2 = self._redis.pipeline()

        pipe2.zadd(key, {request_id: now})
        pipe2.expire(key, window_seconds)

        await pipe2.execute()

        return True

    async def close(self):
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


def get_rate_limiter() -> RateLimiter:
    """Returns the process-wide RateLimiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings.CELERY_RESULT_BACKEND)
    return _rate_limiter
