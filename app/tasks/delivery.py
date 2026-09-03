import logging

from app.celery_app import celery_app
from app.core.async_utils import run_async
from app.core.rate_limiter import get_rate_limiter
from app.db.uow import UnitOfWork
from app.services import DeliveryService, NotificationService


logger = logging.getLogger(__name__)


async def _send_batch(notification_id: int, delivery_ids: list[int]):
    delivery_service = DeliveryService(rate_limiter=get_rate_limiter())
    notification_service = NotificationService(rate_limiter=get_rate_limiter())

    logger.info(
        "Send batch started (notification_id=%s, deliveries=%s)",
        notification_id,
        len(delivery_ids),
    )

    try:
        async with UnitOfWork() as uow:
            await delivery_service.send_deliveries(uow, delivery_ids)
            await notification_service.finalize_notification(uow, notification_id)

            logger.info(
                "Send batch task finished successfully (notification_id=%s)",
                notification_id,
            )
    except Exception:
        logger.exception(
            "Send batch task failed (notification_id=%s)",
            notification_id,
        )
        raise
    finally:
        await delivery_service.provider_registry.close_all()


@celery_app.task
def send_batch_task(notification_id: int, delivery_ids: list[int]):
    run_async(_send_batch(notification_id, delivery_ids))
