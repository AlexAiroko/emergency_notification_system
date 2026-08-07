import pytest_asyncio

from app.services.contact import ContactService


@pytest_asyncio.fixture
async def contact_service():
    return ContactService()
