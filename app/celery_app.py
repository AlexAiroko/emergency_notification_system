import os
from datetime import timedelta

from celery import Celery
from celery.signals import worker_process_shutdown
from kombu import Queue
from prometheus_client import multiprocess

from app.core.config import settings
from app.metrics.registry import multiprocess_dir


celery_app = Celery(
    "notification_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notification",
        "app.tasks.delivery",
        "app.tasks.sweeper",
        "app.tasks.contact_import",
    ],
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

    beat_schedule={
        "sweep-deliveries": {
            "task": "app.tasks.sweeper.sweep_deliveries_task",
            "schedule": timedelta(seconds=settings.SWEEP_INTERVAL_SECONDS),
        },
    },
)


@worker_process_shutdown.connect
def _drop_prometheus_process_metrics(**_kwargs) -> None:
    if multiprocess_dir():
        multiprocess.mark_process_dead(os.getpid())
