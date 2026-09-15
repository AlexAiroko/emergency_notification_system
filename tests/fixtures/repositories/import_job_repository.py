import pytest_asyncio

from app.repositories.import_job import ImportJobRepository


@pytest_asyncio.fixture
async def import_job_repo(db_session):
    return ImportJobRepository(db_session)
