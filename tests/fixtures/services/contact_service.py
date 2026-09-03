import pytest_asyncio

from app.services import ContactService


@pytest_asyncio.fixture
async def contact_service():
    return ContactService()
