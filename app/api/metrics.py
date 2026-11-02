from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.metrics.registry import get_registry


router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(get_registry()),
        media_type=CONTENT_TYPE_LATEST,
    )