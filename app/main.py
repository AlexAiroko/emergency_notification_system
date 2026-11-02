import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from prometheus_client import multiprocess

import app.core.logging
from app.api.exception import error_handler
from app.api.notification_template import router as template_router
from app.api.contact import router as contact_router
from app.api.contact_method import router as contact_method_router
from app.api.group import router as group_router
from app.api.delivery import router as delivery_router
from app.api.notification import router as notification_router
from app.api.metrics import router as metrics_router
from app.core.rate_limiter import get_rate_limiter
from app.db.uow import UnitOfWork
from app.exceptions.base import AppError
from app.metrics.collector import notifications_in_progress
from app.metrics.registry import multiprocess_dir


logger = logging.getLogger(__name__)

IN_PROGRESS_REFRESH_SECONDS = 10


async def _refresh_in_progress_loop() -> None:
    while True:
        try:
            async with UnitOfWork() as uow:
                count = await uow.notification_repo.count_in_progress()
            notifications_in_progress.set(count)
        except Exception:
            logger.exception("Failed to refresh notifications_in_progress")
        await asyncio.sleep(IN_PROGRESS_REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    refresh_task = asyncio.create_task(_refresh_in_progress_loop())
    try:
        yield
    finally:
        refresh_task.cancel()
        with suppress(asyncio.CancelledError):
            await refresh_task
        await get_rate_limiter().close()
        if multiprocess_dir():
            multiprocess.mark_process_dead(os.getpid())


app = FastAPI(lifespan=lifespan)


app.include_router(template_router)
app.include_router(contact_router)
app.include_router(contact_method_router)
app.include_router(group_router)
app.include_router(delivery_router)
app.include_router(notification_router)
app.include_router(metrics_router)

app.add_exception_handler(
    AppError,
    error_handler, # type: ignore[arg-type]
)


@app.get("/health")
def health():
    return {"status": "ok"}
