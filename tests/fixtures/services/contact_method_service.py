import pytest_asyncio

from app.services.contact_method import ContactMethodService


@pytest_asyncio.fixture
async def contact_method_service():
    return ContactMethodService()
