import logging

from app.db.uow import UnitOfWork
from app.services.notification import NotificationService


logger = logging.getLogger(__name__)


async def send_notification_task(notification_id: int):
    logger.info(
        "Background task started (notification_id=%s)",
        notification_id,
    )

    try:
        async with UnitOfWork() as uow:
            await NotificationService().send_notification(
                uow=uow,
                notification_id=notification_id,
            )

        logger.info(
            "Background task finished successfully (notification_id=%s)",
            notification_id,
        )

    except Exception as exc:
        logger.exception(
            "Background task failed (notification_id=%s)",
            notification_id,
        )
        raise
