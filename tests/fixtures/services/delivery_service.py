from unittest.mock import AsyncMock, Mock

import pytest_asyncio

from app.services import DeliveryService


@pytest_asyncio.fixture
async def delivery_service():
    rate_limiter = Mock()
    rate_limiter.acquire = AsyncMock(return_value=True)
    service = DeliveryService(rate_limiter=rate_limiter)
    service.template_service = Mock()
    return service
