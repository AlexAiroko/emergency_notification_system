from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions.contact import ContactAlreadyExistsError, ContactNotFoundError


@pytest.mark.asyncio
async def test_create_contact_success(contact_service, uow):
    contact = SimpleNamespace(id=1, name="John")

    uow.contact_repo.create = AsyncMock(return_value=contact)

    result = await contact_service.create_contact(
        uow=uow,
        name="John",
        external_id="ext-1",
    )

    assert result is contact

    uow.contact_repo.create.assert_called_once_with(
        name="John",
        external_id="ext-1",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_create_contact_already_exists(contact_service, uow):
    uow.contact_repo.create = AsyncMock(
        side_effect=IntegrityError(
            statement="",
            params={},
            orig=Exception(),
        )
    )

    with pytest.raises(ContactAlreadyExistsError):
        await contact_service.create_contact(
            uow=uow,
            name="John",
            external_id="ext-1",
        )


@pytest.mark.asyncio
async def test_get_contact_success(contact_service, uow):
    contact = SimpleNamespace(id=1, name="John")

    uow.contact_repo.get = AsyncMock(return_value=contact)

    result = await contact_service.get_contact(
        uow=uow,
        contact_id=1,
    )

    assert result is contact

    uow.contact_repo.get.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_contact_not_found(contact_service, uow):
    uow.contact_repo.get = AsyncMock(return_value=None)

    with pytest.raises(ContactNotFoundError):
        await contact_service.get_contact(
            uow=uow,
            contact_id=999,
        )

    uow.contact_repo.get.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_update_contact_success(contact_service, uow):
    updated_contact = SimpleNamespace(id=1, name="Old")

    uow.contact_repo.update = AsyncMock(return_value=updated_contact)

    result = await contact_service.update_contact(
        uow=uow,
        contact_id=1,
        name="New Name",
    )

    assert result is updated_contact

    uow.contact_repo.update.assert_called_once_with(
        1,
        name="New Name",
    )


@pytest.mark.asyncio
async def test_update_contact_not_found(contact_service, uow):
    uow.contact_repo.update = AsyncMock(return_value=None)

    with pytest.raises(ContactNotFoundError) as exc:
        await contact_service.update_contact(
            uow=uow,
            contact_id=999,
            name="New Name",
        )

    uow.contact_repo.update.assert_called_once_with(
        999,
        name="New Name",
    )
