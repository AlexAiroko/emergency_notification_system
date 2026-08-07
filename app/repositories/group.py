from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.models.contact import Contact
from app.models.group import Group
from app.models.group_contact import GroupContact
from app.repositories.active import ActiveRepository


class GroupRepository(ActiveRepository):
    model = Group
    
    async def get_with_contacts(self, group_id: int) -> Group | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.contacts))
            .where(self.model.id == group_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
    
    async def add_contact(self, group_id: int, contact_id: int) -> None:
        link = GroupContact(
            group_id=group_id,
            contact_id=contact_id,
        )
        self.session.add(link)
        await self.flush()

    async def remove_contact_from_group(self, group_id: int, contact_id: int) -> None:
        stmt = (
            delete(GroupContact)
            .where(
                GroupContact.group_id == group_id,
                GroupContact.contact_id == contact_id,
            )
        )
        await self.session.execute(stmt)
    
    async def get_contacts_for_dispatch(self, group_id: int) -> list[Contact]:
        stmt = (
            select(Contact)
            .join(GroupContact, GroupContact.contact_id == Contact.id)
            .where(GroupContact.group_id == group_id)
            .options(selectinload(Contact.contact_methods))
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
