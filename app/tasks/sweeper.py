import logging

from app.celery_app import celery_app
from app.core.async_utils import run_async
from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.core.utils import chunk
from app.db.uow import UnitOfWork
from app.services.notification import NotificationService
from app.tasks.delivery import send_batch_task


logger = logging.getLogger(__name__)


async def _sweep_deliveries():
    async with RateLimiter(settings.CELERY_RESULT_BACKEND) as limiter:
        service = NotificationService(rate_limiter=limiter)

        try:
            async with UnitOfWork() as uow:
                groups = await service.claim_due_retries(uow)
                finalized = await service.finalize_stuck_notifications(uow)

            for notification_id, delivery_ids in groups.items():
                for batch in chunk(delivery_ids, settings.DELIVERY_BATCH_SIZE):
                    send_batch_task.delay(notification_id, batch)

            logger.info(
                "Sweep finished (notifications=%s, deliveries=%s)",
                finalized, sum(len(ids) for ids in groups.values()),
            )
        
        except Exception:
            logger.exception("Sweep failed")
            raise
        finally:
            await service.delivery_service.provider_registry.close_all()


@celery_app.task
def sweep_deliveries_task():
    run_async(_sweep_deliveries())
