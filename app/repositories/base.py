from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    model = None
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def flush(self) -> None:
        await self.session.flush()
    
    async def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.flush()
        return obj
    
    async def get(self, obj_id: int):
        stmt = (
            select(self.model)
            .where(self.model.id == obj_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
    
    async def get_many(self, limit: int = 20, offset: int = 0):
        stmt = (
            select(self.model)
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
    
    async def update(
        self,
        obj_id: int,
        **kwargs,
    ):
        obj = await self.get(obj_id)

        if obj is None:
            return None

        for key, value in kwargs.items():
            setattr(obj, key, value)

        await self.flush()

        return obj

    async def delete(self, obj_id: int) -> None:
        obj = await self.get(obj_id)

        if obj is not None:
            await self.session.delete(obj)
