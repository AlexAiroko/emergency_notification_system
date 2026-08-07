from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_maker
from app.db.uow import UnitOfWork


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork() as uow:
        yield uow
