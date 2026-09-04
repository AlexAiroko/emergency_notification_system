import logging

from sqlalchemy.exc import IntegrityError

from app.db.uow import UnitOfWork
from app.exceptions.contact import (
    ContactAlreadyExistsError,
    ContactNotFoundError,
)
from app.models.contact import Contact

logger = logging.getLogger(__name__)


class ContactService:
    async def create_contact(
        self,
        uow: UnitOfWork,
        external_id: str | None,
        name: str,
        is_active: bool = True,
    ) -> Contact:
        """
        Creates a new contact.
        """

        try:
            contact = await uow.contact_repo.create(
                name=name,
                external_id=external_id,
                is_active=is_active,
            )
        except IntegrityError as exc:
            logger.warning(
                "Contact with external_id=%s already exists",
                external_id,
            )
            raise ContactAlreadyExistsError() from exc

        logger.info(
            "Created contact %s (name=%s)",
            contact.id,
            contact.name,
        )

        return contact

    async def get_contact(
        self,
        uow: UnitOfWork,
        contact_id: int,
    ) -> Contact:
        """
        Returns a contact by ID.
        """

        contact = await uow.contact_repo.get(contact_id)
        
        if contact is None:
            logger.warning(
                "Contact %s not found",
                contact_id,
            )
            raise ContactNotFoundError(contact_id)

        return contact

    async def update_contact(
        self,
        uow: UnitOfWork,
        contact_id: int,
        name: str,
    ) -> Contact:
        updated = await uow.contact_repo.update(
            contact_id,
            name=name,
        )

        if updated is None:
            logger.warning(
                "Contact %s not found",
                contact_id,
            )
            raise ContactNotFoundError(contact_id)

        logger.info(
            "Updated contact %s (name=%s)",
            updated.id,
            updated.name,
        )

        return updated

    async def activate_contact(
        self,
        uow: UnitOfWork,
        contact_id: int,
    ) -> None:
        await self.get_contact(uow, contact_id)
        await uow.contact_repo.activate(contact_id)
        logger.info("Contact %s activated", contact_id)

    async def deactivate_contact(
        self,
        uow: UnitOfWork,
        contact_id: int,
    ) -> None:
        await self.get_contact(uow, contact_id)
        await uow.contact_repo.deactivate(contact_id)
        logger.info("Contact %s deactivated", contact_id)
