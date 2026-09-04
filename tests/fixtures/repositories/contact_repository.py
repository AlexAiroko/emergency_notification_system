import pytest_asyncio

from app.repositories import ContactRepository


@pytest_asyncio.fixture
async def contact_repo(db_session):
    return ContactRepository(db_session)
