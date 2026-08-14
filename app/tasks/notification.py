import logging

from app.celery_app import celery_app
from app.core.async_utils import run_async
from app.db.uow import UnitOfWork
from app.services.notification import NotificationService


logger = logging.getLogger(__name__)


async def _send_notification(notification_id: int):
    logger.info(
        "Celery task started (notification_id=%s)",
        notification_id,
    )

    try:
        async with UnitOfWork() as uow:
            await NotificationService().send_notification(
                uow=uow,
                notification_id=notification_id,
            )

        logger.info(
            "Celery task finished successfully (notification_id=%s)",
            notification_id,
        )

    except Exception:
        logger.exception(
            "Celery task failed (notification_id=%s)",
            notification_id,
        )
        raise


@celery_app.task
def send_notification_task(notification_id: int):
    run_async(_send_notification(notification_id))
