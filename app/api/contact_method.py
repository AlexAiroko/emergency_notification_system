from fastapi import APIRouter, Depends, status

from app.db.deps import get_uow
from app.db.uow import UnitOfWork
from app.schemas.contact_method import ContactMethodCreate, ContactMethodResponse, ContactMethodUpdate
from app.services.contact_method import ContactMethodService


router = APIRouter(
    prefix="/contacts/{contact_id}/methods",
    tags=["Contact methods"]
)


@router.post(
    "",
    response_model=ContactMethodResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_method(
    contact_id: int,
    data: ContactMethodCreate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ContactMethodService()
    
    method = await service.create_method(
        uow=uow,
        contact_id=contact_id,
        channel=data.channel,
        address=data.address,
    )
    
    return method


@router.get(
    "",
    response_model=list[ContactMethodResponse]
)
async def get_methods(
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ContactMethodService()
    
    methods = await service.get_methods(
        uow=uow,
        contact_id=contact_id,
    )
    
    return methods


@router.get(
    "/{method_id}",
    response_model=ContactMethodResponse,
)
async def get_method(
    contact_id: int,
    method_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ContactMethodService()
    
    method = await service.get_method(
        uow=uow,
        contact_id=contact_id,
        method_id=method_id,
    )
    
    return method


@router.patch(
    "/{method_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_method(
    contact_id: int,
    method_id: int,
    data: ContactMethodUpdate,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ContactMethodService()
    
    await service.update_method(
        uow=uow,
        contact_id=contact_id,
        method_id=method_id,
        channel=data.channel,
        address=data.address,
        is_active=data.is_active,
    )


@router.delete(
    "/{method_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_method(
    contact_id: int,
    method_id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ContactMethodService()
    
    await service.delete_method(
        uow=uow,
        contact_id=contact_id,
        method_id=method_id,
    )
