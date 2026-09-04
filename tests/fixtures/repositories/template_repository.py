import pytest_asyncio

from app.repositories import NotificationTemplateRepository


@pytest_asyncio.fixture
async def template_repo(db_session):
    return NotificationTemplateRepository(db_session)
