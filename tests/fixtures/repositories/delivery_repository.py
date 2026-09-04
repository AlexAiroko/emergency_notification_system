import pytest_asyncio

from app.repositories import DeliveryRepository


@pytest_asyncio.fixture
async def delivery_repo(db_session):
    return DeliveryRepository(db_session)
