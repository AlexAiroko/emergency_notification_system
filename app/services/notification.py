from datetime import timedelta
import logging

from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.core.utils import utc_now, chunk
from app.db.uow import UnitOfWork
from app.exceptions.delivery import TooManyDeliveriesError
from app.exceptions.notification import NotificationNotFoundError
from app.models.contact import Contact
from app.models.delivery import Delivery, DeliveryStatus
from app.models.notification import Notification, NotificationStatus
from app.services.delivery import DeliveryService
from app.services.group import GroupService
from app.services.notification_template import NotificationTemplateService


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, rate_limiter: RateLimiter) -> None:
        self.delivery_service = DeliveryService(rate_limiter=rate_limiter)
        self.group_service = GroupService()
        self.template_service = NotificationTemplateService()

    async def _prepare_deliveries(
        self,
        contacts: list[Contact],
        notification_id: int,
    ) -> list[Delivery]:
        deliveries = []
        
        for contact in contacts:
            for method in contact.contact_methods:
                if method.is_active:
                    deliveries.append(
                        Delivery(
                            notification_id=notification_id,
                            contact_id=contact.id,
                            contact_method_id=method.id,
                            channel=method.channel,
                            address=method.address,
                            status=DeliveryStatus.PENDING,
                        )
                    )

        return deliveries

    async def create_notification(
        self,
        uow: UnitOfWork,
        template_id: int,
        group_id: int,
    ) -> Notification:
        """
        Creates a Notification with the PENDING status and generates a Delivery
        for each ContactMethod of each contact in the group.
        """

        await self.template_service.ensure_template_is_active(
            uow,
            template_id,
        )

        await self.group_service.ensure_group_is_active(uow, group_id)

        notification = await uow.notification_repo.create(
            template_id=template_id,
            group_id=group_id,
        )

        logger.info(
            "Created notification %s (template=%s, group=%s)",
            notification.id,
            template_id,
            group_id,
        )

        contacts = await uow.group_repo.get_contacts_for_dispatch(group_id)

        logger.info(
            "Found %s contacts for notification %s",
            len(contacts),
            notification.id,
        )

        deliveries = await self._prepare_deliveries(contacts, notification.id)

        if not deliveries:
            logger.warning(
                "Notification %s has no recipient",
                notification.id,
            )
            return notification

        if len(deliveries) > settings.MAX_DELIVERIES_PER_NOTIFICATION:
            raise TooManyDeliveriesError(
                len(deliveries),
                settings.MAX_DELIVERIES_PER_NOTIFICATION,
            )

        await uow.delivery_repo.create_bulk(deliveries)

        logger.info(
            "Prepared %s deliveries for notification %s",
            len(deliveries),
            notification.id,
        )

        return notification

    async def start_notification(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> None:
        notification = await uow.notification_repo.get(notification_id)
        
        if notification is None:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            raise NotificationNotFoundError(notification_id)

        await uow.notification_repo.mark_started(notification_id)

    async def prepare_batches(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> list[list[int]]:
        delivery_ids = await uow.delivery_repo.get_ready_for_dispatch(notification_id)
        batches = chunk(delivery_ids, settings.DELIVERY_BATCH_SIZE)
        return batches

    async def finalize_notification(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> None:
        """
        Calculates the final Notification status based on Delivery statistics.

        Rules:
        - all SENT -> SUCCESS
        - all FAILED -> FAILED
        - part SENT and part FAILED -> PARTIAL_SUCCESS
        """

        stats = await uow.delivery_repo.get_stats(notification_id)

        sent = stats.get("sent", 0)
        failed = stats.get("failed", 0)
        pending = stats.get("pending", 0)
        total = sent + failed

        if pending > 0:
            logger.warning(
                "Notification %s has %s pending deliveries, skipping finalization",
                notification_id, pending,
            )
            return

        if total == 0:
            logger.warning(
                "Finished notification %s without deliveries",
                notification_id,
            )
            status = NotificationStatus.SUCCESS
        elif sent == total:
            status = NotificationStatus.SUCCESS
        elif failed == total:
            status = NotificationStatus.FAILED
        else:
            status = NotificationStatus.PARTIAL_SUCCESS

        await uow.notification_repo.update_status(
            notification_id,
            status,
        )

        logger.info(
            "Finalized notification %s (status=%s, sent=%s, failed=%s)",
            notification_id,
            status.value,
            sent,
            failed,
        )

    async def get_notification(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> Notification:
        notification = await uow.notification_repo.get_with_relations(notification_id)

        if notification is None:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            raise NotificationNotFoundError(notification_id)

        return notification

    async def claim_due_retries(self, uow: UnitOfWork) -> dict[int, list[int]]:
        """Captures mature retries, groups them by notification_id."""

        next_attempt_at = utc_now() + timedelta(
            seconds=settings.RETRY_INTERVAL_SECONDS,
        )

        deliveries = await uow.delivery_repo.claim_deliveries_for_retry(next_attempt_at)

        groups: dict[int, list[int]] = {}
        for delivery in deliveries:
            groups.setdefault(delivery.notification_id, []).append(delivery.id)
        return groups

    async def finalize_stuck_notifications(self, uow: UnitOfWork) -> int:
        stuck = await uow.notification_repo.get_stuck_in_progress_ids()
        for notification_id in stuck:
            await self.finalize_notification(uow, notification_id)
        return len(stuck)

