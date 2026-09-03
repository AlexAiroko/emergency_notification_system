from fastapi import APIRouter, Depends, File, UploadFile, status

from app.db.deps import get_contact_import_service, get_contact_service, get_uow
from app.db.uow import UnitOfWork
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from app.schemas.contact_import import ContactImportResponse, ImportErrorItem
from app.services import ContactService, ContactImportService


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    data: ContactCreate,
    uow: UnitOfWork = Depends(get_uow),
    service: ContactService = Depends(get_contact_service),
):
    return await service.create_contact(
        uow=uow,
        external_id=data.external_id,
        name=data.name,
    )


@router.get(
    "",
    response_model=list[ContactResponse],
)
async def get_many_contacts(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.contact_repo.get_many(
        limit=limit,
        offset=offset,
    )


@router.get(
    "/active",
    response_model=list[ContactResponse],
)
async def get_active_contacts(
    limit: int = 20,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.contact_repo.get_active(
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
)
async def get_contact_by_id(
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: ContactService = Depends(get_contact_service),
):
    return await service.get_contact(uow, contact_id)


@router.patch(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    uow: UnitOfWork = Depends(get_uow),
    service: ContactService = Depends(get_contact_service),
):
    await service.update_contact(
        uow=uow,
        contact_id=contact_id,
        name=data.name,
    )


@router.patch(
    "/{contact_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def activate_contact(
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: ContactService = Depends(get_contact_service),
):
    await service.activate_contact(uow, contact_id)


@router.patch(
    "/{contact_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_contact(
    contact_id: int,
    uow: UnitOfWork = Depends(get_uow),
    service: ContactService = Depends(get_contact_service),
):
    await service.deactivate_contact(uow, contact_id)


@router.post(
    "/import",
    response_model=ContactImportResponse,
)
async def import_contacts(
    file: UploadFile = File(),
    uow: UnitOfWork = Depends(get_uow),
    service: ContactImportService = Depends(get_contact_import_service),
):
    result = await service.import_contacts(uow, file)
    
    return ContactImportResponse(
        message="Contacts import completed",
        total=result.total,
        imported=result.imported,
        skipped=result.skipped,
        errors=[
            ImportErrorItem(**err)
            for err in result.errors
        ],
    )
