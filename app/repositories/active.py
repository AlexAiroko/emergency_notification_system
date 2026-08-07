from sqlalchemy import select

from app.repositories.base import BaseRepository


class ActiveRepository(BaseRepository):
    """
    Repository for models with is_active field
    """
    
    async def get_active(
        self,
        limit: int = 20,
        offset: int = 0,
    ):
        stmt = (
            select(self.model)
            .where(self.model.is_active.is_(True))
            .order_by(self.model.id)
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
    
    async def activate(self, obj_id: int) -> None:
        await self.update(obj_id, is_active=True)
    
    async def deactivate(self, obj_id: int) -> None:
        await self.update(obj_id, is_active=False)
