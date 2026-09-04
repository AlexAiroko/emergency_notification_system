import logging

from fastapi import APIRouter, Depends, status

from app.db.deps import get_notification_service, get_uow
from app.db.uow import UnitOfWork
from app.schemas.delivery import DeliveryResponse
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services import NotificationService
from app.tasks.notification import send_notification_task


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    data: NotificationCreate,
    uow: UnitOfWork = Depends(get_uow),
    service: NotificationService = Depends(get_notification_service),
):
    return await service.create_notification(
        uow=uow,
        template_id=data.template_id,
        group_id=data.group_id,
    )


@router.get(
    "",
    response_model=list[NotificationResponse],
)
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.notification_repo.get_many(
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: NotificationService = Depends(get_notification_service),
):
    return await service.get_notification(uow, notification_id)


@router.post(
    "/{notification_id}",
)
def send_notification(
    notification_id: int,
):
    logger.info("Enqueuing notification %s", notification_id)
    send_notification_task.delay(notification_id)
    return {"message": "Notification started"}


@router.get(
    "/{notification_id}/deliveries",
    response_model=list[DeliveryResponse],
)
async def get_deliveries(
    notification_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.delivery_repo.get_by_notification(notification_id)


@router.get("/{notification_id}/stats")
async def get_notification_stats(
    notification_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.delivery_repo.get_stats(notification_id)
