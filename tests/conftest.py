from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base

pytest_plugins = [
    "tests.fixtures.models.contact",
    "tests.fixtures.models.contact_method",
    "tests.fixtures.models.group",
    "tests.fixtures.models.delivery",
    "tests.fixtures.models.notification_template",
    "tests.fixtures.models.notification",

    "tests.fixtures.repositories.contact_repository",
    "tests.fixtures.repositories.contact_method_repository",
    "tests.fixtures.repositories.group_repository",
    "tests.fixtures.repositories.delivery_repository",
    "tests.fixtures.repositories.template_repository",
    "tests.fixtures.repositories.notification_repository",

    "tests.fixtures.services.contact_service",
    "tests.fixtures.services.contact_method_service",
    "tests.fixtures.services.group_service",
    "tests.fixtures.services.delivery_service",
    "tests.fixtures.services.template_service",
    "tests.fixtures.services.notification_service",

    "tests.fixtures.uow",
]

engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:

    async with SessionLocal() as session:
        yield session
