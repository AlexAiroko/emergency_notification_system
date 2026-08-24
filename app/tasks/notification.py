import logging

from app.celery_app import celery_app
from app.core.async_utils import run_async
from app.db.uow import UnitOfWork
from app.services.notification import NotificationService
from app.tasks.delivery import send_batch_task


logger = logging.getLogger(__name__)


async def _dispatch_notification(notification_id: int):
    service = NotificationService()

    logger.info(
        "Dispatching notification %s",
        notification_id,
    )

    try:
        async with UnitOfWork() as uow:
            await service.start_notification(
                uow=uow,
                notification_id=notification_id,
            )

            batches = await service.prepare_batches(uow, notification_id)
        if not batches:
            logger.info(
                "Notification %s has no ready deliveries, finalizing immediately",
                notification_id,
            )

            async with UnitOfWork() as uow:
                await service.finalize_notification(uow, notification_id)
            return
        
        for batch in batches:
            send_batch_task.delay(notification_id, batch)

        logger.info(
            "Enqueued %s batches (%s deliveries) for notification %s",
            len(batches),
            sum(len(batch) for batch in batches),
            notification_id,
        )

    except Exception:
        logger.exception(
            "Send notification task failed (notification_id=%s)",
            notification_id,
        )
        raise
    finally:
        await service.delivery_service.provider_registry.close_all()


@celery_app.task
def send_notification_task(notification_id: int):
    run_async(_dispatch_notification(notification_id))
