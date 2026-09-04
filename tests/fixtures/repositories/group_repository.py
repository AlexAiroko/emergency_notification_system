import pytest_asyncio

from app.repositories import GroupRepository


@pytest_asyncio.fixture
async def group_repo(db_session):
    return GroupRepository(db_session)
