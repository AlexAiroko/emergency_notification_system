from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.metrics.registry import get_metrics_collector


router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    collector = get_metrics_collector()
    return collector.render()
