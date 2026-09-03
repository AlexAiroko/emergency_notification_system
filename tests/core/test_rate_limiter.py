from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.rate_limiter import RateLimiter, get_rate_limiter


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_acquire_allows_first_request(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe = Mock()
    pipe.execute = AsyncMock(return_value=[0, 0])
    mock_redis.pipeline.return_value = pipe

    limiter = RateLimiter("redis://test")
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

    limiter = RateLimiter("redis://test")
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

    limiter = RateLimiter("redis://test")
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

    limiter = RateLimiter("redis://test")
    result_first = await limiter.acquire("rate_limit:email", 50, 60)
    result_second = await limiter.acquire("rate_limit:email", 50, 60)

    assert result_first is False
    assert result_second is True


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_rate_limiter_lazy_connect(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    pipe = Mock()
    pipe.execute = AsyncMock(return_value=[0, 0])
    mock_redis.pipeline.return_value = pipe

    limiter = RateLimiter("redis://test")

    assert limiter._redis is None

    await limiter.acquire("rate_limit:email", 50, 60)

    mock_aioredis.from_url.assert_called_once_with(
        "redis://test",
        decode_responses=True,
    )
    assert limiter._redis is mock_redis


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_rate_limiter_connect_is_idempotent(mock_aioredis):
    mock_redis = Mock()
    mock_aioredis.from_url.return_value = mock_redis

    limiter = RateLimiter("redis://test")

    await limiter.connect()
    await limiter.connect()

    mock_aioredis.from_url.assert_called_once()


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_rate_limiter_close(mock_aioredis):
    mock_redis = Mock()
    mock_redis.aclose = AsyncMock()
    mock_aioredis.from_url.return_value = mock_redis

    limiter = RateLimiter("redis://test")
    await limiter.connect()

    assert limiter._redis is mock_redis

    await limiter.close()

    mock_redis.aclose.assert_awaited_once()
    assert limiter._redis is None


@pytest.mark.asyncio
@patch("app.core.rate_limiter.aioredis")
async def test_rate_limiter_close_when_not_connected(mock_aioredis):
    limiter = RateLimiter("redis://test")

    await limiter.close()

    mock_aioredis.from_url.assert_not_called()


@patch("app.core.rate_limiter._rate_limiter", None)
@patch("app.core.rate_limiter.settings")
def test_get_rate_limiter_singleton(mock_settings):
    mock_settings.CELERY_RESULT_BACKEND = "redis://test"

    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()

    assert limiter1 is limiter2
    assert isinstance(limiter1, RateLimiter)
