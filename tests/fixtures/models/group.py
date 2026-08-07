import pytest_asyncio

from app.models.group import Group


@pytest_asyncio.fixture
async def group(db_session):
    group = Group(name="G1")
    db_session.add(group)
    await db_session.flush()
    return group
