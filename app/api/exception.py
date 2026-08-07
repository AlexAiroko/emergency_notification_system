from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.base import AppError


async def error_handler(
    request: Request,
    exc: AppError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": str(exc),
        },
    )
