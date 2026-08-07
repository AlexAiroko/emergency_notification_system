from unittest.mock import Mock

import pytest_asyncio

from app.services.notification import NotificationService


@pytest_asyncio.fixture
async def notification_service():
    """
    Creates a NotificationService with mocked inner services.
    """
    service = NotificationService()

    service.delivery_service = Mock()
    service.template_service = Mock()

    return service
