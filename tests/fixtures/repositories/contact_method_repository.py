import pytest_asyncio

from app.repositories import ContactMethodRepository


@pytest_asyncio.fixture
async def contact_method_repo(db_session):
    return ContactMethodRepository(db_session)
