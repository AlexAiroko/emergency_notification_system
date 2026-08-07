from unittest.mock import Mock

import pytest_asyncio

from app.services.delivery import DeliveryService


@pytest_asyncio.fixture
async def delivery_service():
    service = DeliveryService()
    service.template_service = Mock()
    return service
