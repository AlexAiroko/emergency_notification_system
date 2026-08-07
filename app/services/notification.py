import logging

from app.db.uow import UnitOfWork
from app.exceptions.notification import NotificationNotFoundError
from app.models.delivery import Delivery, DeliveryStatus
from app.models.notification import Notification, NotificationStatus
from app.services.delivery import DeliveryService
from app.services.group import GroupService
from app.services.notification_template import NotificationTemplateService

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        self.delivery_service = DeliveryService()
        self.group_service = GroupService()
        self.template_service = NotificationTemplateService()

    async def _prepare_deliveries(
        self,
        contacts,
        notification_id: int,
    ) -> list[Delivery]:
        deliveries = []
        
        for contact in contacts:
            for method in contact.contact_methods:
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

        await self.group_service.get_group(uow, group_id)

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

        await uow.delivery_repo.create_bulk(deliveries)

        logger.info(
            "Prepared %s deliveries for notification %s",
            len(deliveries),
            notification.id,
        )

        return notification

    async def send_notification(
        self,
        uow: UnitOfWork,
        notification_id: int,
    ) -> None:
        """
        The full notification sending cycle:
        1. Sets the notification to IN_PROGRESS
        2. Sends all pending deliveries
        3. Finalizes the notification status
        """

        logger.info(
            "Started sending notification %s",
            notification_id,
        )

        notification = await uow.notification_repo.get(notification_id)

        if notification is None:
            logger.warning(
                "Notification %s not found",
                notification_id,
            )
            raise NotificationNotFoundError(notification_id)


        await uow.notification_repo.mark_started(notification_id)

        try:
            await self.delivery_service.send_pending(
                uow,
                notification_id,
            )
        except Exception:
            logger.exception(
                "Unexpected error while sending notification %s",
                notification_id,
            )
            raise
        finally:
            await self.finalize_notification(
                uow,
                notification_id,
            )

        logger.info(
            "Finished sending notification %s",
            notification_id,
        )

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

        total = sent + failed

        if total == 0:
            logger.warning(
                "Finished notification %s without deliveries",
                notification_id,
            )
            return

        if sent == total:
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
