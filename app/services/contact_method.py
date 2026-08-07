import logging

from app.db.uow import UnitOfWork
from app.exceptions.base import ValidationError
from app.exceptions.contact import ContactNotFoundError
from app.exceptions.contact_method import ContactMethodNotFoundError
from app.models.contact_method import ChannelType, ContactMethod
from app.services.contact import ContactService
from app.validators.contact_methods.registry import ContactMethodValidatorRegistry

logger = logging.getLogger(__name__)


class ContactMethodService:
    def __init__(self) -> None:
        self.contact_service = ContactService()
    
    async def _get_contact_method(
        self,
        uow: UnitOfWork,
        contact_id: int,
        method_id: int,
    ) -> ContactMethod:
        method = await uow.contact_method_repo.get(method_id)

        if method is None or method.contact_id != contact_id:
            logger.warning(
                "Contact method %s not found for contact %s",
                method_id,
                contact_id,
            )
            raise ContactMethodNotFoundError(method_id)

        return method
    
    async def create_method(
        self,
        uow: UnitOfWork,
        contact_id: int,
        channel: ChannelType,
        address: str,
    ) -> ContactMethod:
        await self.contact_service.get_contact(uow, contact_id)

        address = ContactMethodValidatorRegistry.validate(
            channel=channel,
            value=address,
        )

        method = await uow.contact_method_repo.create(
            contact_id=contact_id,
            channel=channel,
            address=address,
        )

        logger.info(
            "Created contact method %s for contact %s",
            method.id,
            contact_id,
        )

        return method

    async def get_method(
        self,
        uow: UnitOfWork,
        contact_id: int,
        method_id: int,
    ) -> ContactMethod:
        return await self._get_contact_method(
            uow,
            contact_id,
            method_id,
        )

    async def get_methods(
        self,
        uow: UnitOfWork,
        contact_id: int,
    ) -> list[ContactMethod]:
        await self.contact_service.get_contact(uow, contact_id)

        return await uow.contact_method_repo.get_by_contact(contact_id)

    async def update_method(
        self,
        uow: UnitOfWork,
        contact_id: int,
        method_id: int,
        channel: ChannelType,
        address: str,
        is_active: bool,
    ) -> ContactMethod:
        await self._get_contact_method(
            uow,
            contact_id,
            method_id,
        )

        address = ContactMethodValidatorRegistry.validate(
            channel=channel,
            value=address,
        )

        updated = await uow.contact_method_repo.update(
            method_id,
            channel=channel,
            address=address,
            is_active=is_active,
        )

        logger.info(
            "Updated contact method %s",
            method_id,
        )

        return updated

    async def delete_method(
        self,
        uow: UnitOfWork,
        contact_id: int,
        method_id: int,
    ) -> None:
        await self._get_contact_method(
            uow,
            contact_id,
            method_id,
        )

        await uow.contact_method_repo.delete(method_id)

        logger.info(
            "Deleted contact method %s",
            method_id,
        )
