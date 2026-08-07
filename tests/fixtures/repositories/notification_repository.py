import pytest_asyncio

from app.repositories.notification import NotificationRepository


@pytest_asyncio.fixture
async def notification_repo(db_session):
    return NotificationRepository(db_session)
