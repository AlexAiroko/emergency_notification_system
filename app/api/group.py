from fastapi import APIRouter, Depends, status

from app.db.deps import get_group_service, get_uow
from app.db.uow import UnitOfWork
from app.schemas.contact import ContactResponse
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate, GroupWithContactsResponse
from app.services import GroupService


router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
)


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    data: GroupCreate,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    return await service.create_group(
        uow=uow,
        name=data.name,
    )


@router.get(
    "/{group_id}",
    response_model=GroupWithContactsResponse,
)
async def get_group(
    group_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    return await service.get_group(
        uow=uow,
        group_id=group_id,
    )


@router.get(
    "",
    response_model=list[GroupResponse],
)
async def get_groups(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    return await service.get_many_groups(
        uow,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    await service.update_group(
        uow=uow,
        group_id=group_id,
        name=data.name,
    )


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group(
    group_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    await service.delete_group(
        uow=uow,
        group_id=group_id,
    )


@router.post(
    "/{group_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_contact_to_group(
    group_id: int,
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    await service.add_contact(
        uow=uow,
        group_id=group_id,
        contact_id=contact_id,
    )


@router.delete(
    "/{group_id}/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_contact_from_group(
    group_id: int,
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    await service.remove_contact(
        uow=uow,
        group_id=group_id,
        contact_id=contact_id,
    )


@router.get(
    "/{group_id}/contacts",
    response_model=list[ContactResponse],
)
async def get_group_contacts(
    group_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: GroupService = Depends(get_group_service),
):
    return await service.get_contacts(
        uow=uow,
        group_id=group_id,
    )
