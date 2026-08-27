from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.rate_limiter import RateLimiter


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_acquire_allows_first_request(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe = Mock()
    pipe.execute = AsyncMock(return_value=[0, 0])
    mock_redis.pipeline.return_value = pipe
    mock_redis.aclose = AsyncMock()

    async with RateLimiter("redis://test") as limiter:
        result = await limiter.acquire("rate_limit:email", 50, 60)

    assert result is True

    pipe.zadd.assert_called_once()
    pipe.expire.assert_called_once_with("rate_limit:email", 60)


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_acquire_allows_within_limit(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe = Mock()
    pipe.execute = AsyncMock(return_value=[0, 49])
    mock_redis.pipeline.return_value = pipe
    mock_redis.aclose = AsyncMock()

    async with RateLimiter("redis://test") as limiter:
        result = await limiter.acquire("rate_limit:email", 50, 60)

    assert result is True


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_acquire_rejects_over_limit(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe = Mock()
    pipe.execute = AsyncMock(return_value=[0, 50])
    mock_redis.pipeline.return_value = pipe
    mock_redis.aclose = AsyncMock()

    async with RateLimiter("redis://test") as limiter:
        result = await limiter.acquire("rate_limit:email", 50, 60)

    assert result is False

    assert pipe.zadd.call_count == 0
    assert pipe.expire.call_count == 0


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_acquire_resets_after_window(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe_at_limit = Mock()
    pipe_at_limit.execute = AsyncMock(return_value=[0, 50])

    pipe_after_reset_read = Mock()
    pipe_after_reset_read.execute = AsyncMock(return_value=[0, 10])

    pipe_after_reset_write = Mock()
    pipe_after_reset_write.execute = AsyncMock(return_value=[None, None])

    mock_redis.pipeline.side_effect = [
        pipe_at_limit,
        pipe_after_reset_read,
        pipe_after_reset_write,
    ]
    mock_redis.aclose = AsyncMock()

    async with RateLimiter("redis://test") as limiter:
        result_first = await limiter.acquire("rate_limit:email", 50, 60)
        result_second = await limiter.acquire("rate_limit:email", 50, 60)

    assert result_first is False
    assert result_second is True


@pytest.mark.asyncio
async def test_acquire_raises_if_not_initialized():
    limiter = RateLimiter("redis://test")

    with pytest.raises(RuntimeError, match="RateLimiter is not initialized"):
        await limiter.acquire("rate_limit:email", 50, 60)


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_aexit_closes_redis(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis
    mock_redis.aclose = AsyncMock()

    async with RateLimiter("redis://test") as _:
        pass

    mock_redis.aclose.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_aexit_closes_redis_on_exception(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis
    mock_redis.aclose = AsyncMock()

    with pytest.raises(RuntimeError):
        async with RateLimiter("redis://test") as _:
            raise RuntimeError("test error")

    mock_redis.aclose.assert_awaited_once()
