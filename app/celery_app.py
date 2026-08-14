from celery import Celery
from kombu import Queue

from app.core.config import settings


celery_app = Celery(
    "notification_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.notification"],
)

celery_app.conf.update(
    task_default_queue="notifications",
    task_queues=(
        Queue(
            "notifications",
            durable=True,
        ),
    ),

    task_create_missing_queues=False,

    worker_mingle=False,
    worker_enable_remote_control=False,

    worker_ack_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    task_time_limit=600,
    task_soft_time_limit=540,
)
