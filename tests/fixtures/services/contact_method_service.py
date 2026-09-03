import pytest_asyncio

from app.services import ContactMethodService


@pytest_asyncio.fixture
async def contact_method_service():
    return ContactMethodService()
