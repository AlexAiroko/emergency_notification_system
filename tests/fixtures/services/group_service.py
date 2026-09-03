import pytest_asyncio

from app.services import GroupService


@pytest_asyncio.fixture
async def group_service():
    return GroupService()
