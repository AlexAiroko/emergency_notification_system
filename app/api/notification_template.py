from fastapi import APIRouter, Depends, status

from app.db.deps import get_uow
from app.db.uow import UnitOfWork
from app.schemas.notification_template import NotificationTemplateCreate, NotificationTemplateResponse, NotificationTemplateUpdate
from app.services.notification_template import NotificationTemplateService


router = APIRouter(
    prefix="/templates",
    tags=["Templates"],
)


@router.post(
    "",
    response_model=NotificationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    data: NotificationTemplateCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()
    
    template = await service.create_template(
        uow=uow,
        name=data.name,
        subject=data.subject,
        body=data.body,
        is_active=data.is_active,
    )
    
    return template


@router.get(
    "",
    response_model=list[NotificationTemplateResponse],
)
async def get_many_templates(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()

    templates = await service.get_many_templates(uow, limit, offset)
    
    return templates


@router.get(
    "/active",
    response_model=list[NotificationTemplateResponse],
)
async def get_active_templates(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()

    templates = await service.get_active_templates(uow, limit, offset)
    
    return templates


@router.get(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
)
async def get_template_by_id(
    template_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()

    template = await service.get_template(uow, template_id)
    
    return template


@router.patch(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_template(
    template_id: int,
    data: NotificationTemplateUpdate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()
    
    await service.update_template(
        uow,
        template_id,
        data.subject,
        data.body,
    )


@router.patch(
    "/{template_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def activate_template(
    template_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()
    await service.activate_template(
        uow,
        template_id,
    )


@router.patch(
    "/{template_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_template(
    template_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = NotificationTemplateService()
    await service.deactivate_template(
        uow,
        template_id,
    )
