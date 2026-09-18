from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Contact
from app.repositories.active import ActiveRepository


class ContactRepository(ActiveRepository):
    model = Contact
    
    async def get_with_methods(self, contact_id: int) -> Contact | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.contact_methods))
            .where(self.model.id == contact_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Contact | None:
        stmt = select(self.model).where(self.model.external_id == external_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
