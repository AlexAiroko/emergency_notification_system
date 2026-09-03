from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception import error_handler
from app.api.notification_template import router as template_router
from app.api.contact import router as contact_router
from app.api.contact_method import router as contact_method_router
from app.api.group import router as group_router
from app.api.delivery import router as delivery_router
from app.api.notification import router as notification_router
from app.api.metrics import router as metrics_router
from app.core.rate_limiter import get_rate_limiter
from app.exceptions.base import AppError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await get_rate_limiter().close()


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
