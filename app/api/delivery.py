from fastapi import APIRouter, Depends

from app.db.deps import get_delivery_service, get_uow
from app.db.uow import UnitOfWork
from app.schemas.delivery import DeliveryResponse
from app.services import DeliveryService


router = APIRouter(
    prefix="/deliveries",
    tags=["Deliveries"],
)


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
)
async def get_delivery(
    delivery_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: DeliveryService = Depends(get_delivery_service),
):
    return await service.get_delivery(
        uow=uow,
        delivery_id=delivery_id,
    )
