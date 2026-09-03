from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import get_rate_limiter
from app.db.session import session_maker
from app.db.uow import UnitOfWork
from app.services import (
    ContactService,
    ContactImportService,
    ContactMethodService,
    DeliveryService,
    GroupService,
    NotificationService,
    NotificationTemplateService,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    async with UnitOfWork() as uow:
        yield uow


def get_notification_service() -> NotificationService:
    return NotificationService(rate_limiter=get_rate_limiter())


def get_delivery_service() -> DeliveryService:
    return DeliveryService(rate_limiter=get_rate_limiter())


def get_contact_service() -> ContactService:
    return ContactService()


def get_contact_method_service() -> ContactMethodService:
    return ContactMethodService()


def get_group_service() -> GroupService:
    return GroupService()


def get_template_service() -> NotificationTemplateService:
    return NotificationTemplateService()


def get_contact_import_service() -> ContactImportService:
    return ContactImportService()
