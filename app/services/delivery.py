from datetime import datetime, timedelta, timezone
import logging

from app.core.config import settings
from app.db.uow import UnitOfWork
from app.exceptions.delivery import DeliveryNotFoundError
from app.exceptions.notification import NotificationNotFoundError
from app.models.delivery import Delivery, DeliveryStatus
from app.providers.base import ProviderError
from app.providers.provider_registry import ProviderRegistry
from app.services.notification_template import NotificationTemplateService

logger = logging.getLogger(__name__)


class DeliveryService:
    def __init__(self) -> None:
        self.template_service = NotificationTemplateService()
        self.provider_registry = ProviderRegistry()

    async def _get_delivery(
        self,
        uow: UnitOfWork,
        delivery_id: int,
    ) -> Delivery:
        delivery = await uow.delivery_repo.get(delivery_id)
        
        if delivery is None:
            logger.warning(
                "Delivery %s not found",
                delivery_id,
            )
            raise DeliveryNotFoundError(delivery_id)

        return delivery

    async def get_delivery(
        self,
        uow: UnitOfWork,
        delivery_id: int,
    ) -> Delivery:
        return await self._get_delivery(uow, delivery_id)

    async def send_delivery(
        self,
        uow: UnitOfWork,
        delivery_id: int,
    ) -> None:
        """
        Sends one Delivery.
        """

        delivery = await self._get_delivery(uow, delivery_id)

        notification = await uow.notification_repo.get_with_relations(
            delivery.notification_id,
        )

        if notification is None:
            logger.warning(
                "Notification %s not found",
                delivery.notification_id,
            )
            raise NotificationNotFoundError(delivery.notification_id)

        template = await self.template_service.ensure_template_is_active(
            uow,
            notification.template_id,
        )

        logger.info(
            "Started delivery %s (channel=%s)",
            delivery.id,
            delivery.channel,
        )

        try:
            provider = self.provider_registry.get(delivery.channel)

            provider_message_id = await provider.send(
                to=delivery.address,
                subject=template.subject,
                body=template.body,
            )

            await uow.delivery_repo.mark_sent(
                delivery.id,
                provider_message_id=provider_message_id,
            )

            logger.info(
                "Sent delivery %s",
                delivery.id,
            )

        except ProviderError as exc:
            if delivery.attempts < settings.RETRY_COUNT:
                next_attempt_at = (
                    datetime.now(timezone.utc) + 
                    timedelta(seconds=settings.RETRY_INTERVAL_SECONDS)
                )
                await uow.delivery_repo.mark_retry(delivery.id, next_attempt_at, error_message=str(exc))
                logger.info(
                    "Delivery %s scheduled retry (attempt %s/%s)",
                    delivery.id, delivery.attempts + 1, settings.RETRY_COUNT
                )
            else:
                await uow.delivery_repo.mark_failed(
                    delivery.id,
                    error_message=str(exc),
                )
                logger.exception(
                    "Failed delivery %s",
                    delivery.id,
                )

    async def send_pending(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> None:
        """
        Sends all Deliveries with a PENDING status.
        """

        deliveries = await uow.delivery_repo.get_by_notification(notification_id)

        pending = [
            delivery
            for delivery in deliveries
            if delivery.status == DeliveryStatus.PENDING
        ]

        logger.info(
            "Found %s pending deliveries for notification %s",
            len(pending),
            notification_id,
        )

        for delivery in pending:
            await self.send_delivery(uow, delivery.id)

        logger.info(
            "Finished processing pending deliveries for notification %s",
            notification_id,
        )
