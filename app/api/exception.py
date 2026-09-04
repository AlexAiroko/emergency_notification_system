import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AppError


logger = logging.getLogger(__name__)


async def error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    logger.error(
        "AppError [%s] %s %s → %s",
        exc.code,
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": str(exc),
        },
    )
