from unittest.mock import AsyncMock, Mock

import pytest_asyncio

from app.services import NotificationService


@pytest_asyncio.fixture
async def notification_service():
    rate_limiter = Mock()
    rate_limiter.acquire = AsyncMock(return_value=True)
    service = NotificationService(rate_limiter=rate_limiter)
    service.delivery_service = Mock()
    service.template_service = Mock()
    return service
