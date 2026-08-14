from sqlalchemy import select

from app.models.contact_method import ChannelType, ContactMethod
from app.repositories.active import ActiveRepository


class ContactMethodRepository(ActiveRepository):
    model = ContactMethod
    
    async def get_by_contact(self, contact_id: int) -> list[ContactMethod]:
        stmt = (
            select(self.model)
            .where(self.model.contact_id == contact_id)
            .order_by(self.model.id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_contact_and_channel(
            self,
            contact_id: int,
            channel: ChannelType,
    ) -> list[ContactMethod]:
        stmt = (
            select(self.model)
            .where(
                self.model.contact_id == contact_id,
                self.model.channel == channel,
            )
            .order_by(self.model.id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
