import pytest_asyncio

from app.services import NotificationTemplateService


@pytest_asyncio.fixture
async def template_service():
    return NotificationTemplateService()
