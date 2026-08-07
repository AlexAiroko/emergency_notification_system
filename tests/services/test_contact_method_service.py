from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.exceptions.contact import ContactNotFoundError
from app.exceptions.contact_method import ContactMethodNotFoundError
from app.models.contact_method import ChannelType


@pytest.mark.asyncio
async def test_create_method(contact_method_service, uow):
    contact = SimpleNamespace(id=1)
    method = SimpleNamespace(id=10)

    uow.contact_repo.get = AsyncMock(return_value=contact)
    uow.contact_method_repo.create = AsyncMock(return_value=method)

    result = await contact_method_service.create_method(
        uow,
        contact_id=1,
        channel=ChannelType.EMAIL,
        address="user@mail.com",
    )

    assert result is method

    uow.contact_repo.get.assert_called_once_with(1)
    uow.contact_method_repo.create.assert_called_once_with(
        contact_id=1,
        channel=ChannelType.EMAIL,
        address="user@mail.com",
    )


@pytest.mark.asyncio
async def test_create_method_contact_not_found(contact_method_service, uow):
    uow.contact_repo.get = AsyncMock(return_value=None)
    uow.contact_method_repo.create = AsyncMock()

    with pytest.raises(ContactNotFoundError, match="Contact 1 not found"):
        await contact_method_service.create_method(
            uow,
            contact_id=1,
            channel=ChannelType.EMAIL,
            address="user@mail.com",
        )

    uow.contact_method_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_method(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=1,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)

    result = await contact_method_service.get_method(
        uow,
        contact_id=1,
        method_id=10,
    )

    assert result is method

    uow.contact_method_repo.get.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_get_method_not_found(contact_method_service, uow):
    uow.contact_method_repo.get = AsyncMock(return_value=None)

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.get_method(
            uow,
            contact_id=1,
            method_id=10,
        )


@pytest.mark.asyncio
async def test_get_method_belongs_to_other_contact(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=999,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.get_method(
            uow,
            contact_id=1,
            method_id=10,
        )


@pytest.mark.asyncio
async def test_get_methods(contact_method_service, uow):
    contact = SimpleNamespace(id=1)
    methods = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    uow.contact_repo.get = AsyncMock(return_value=contact)
    uow.contact_method_repo.get_by_contact = AsyncMock(return_value=methods)

    result = await contact_method_service.get_methods(
        uow,
        contact_id=1,
    )

    assert result == methods

    uow.contact_repo.get.assert_called_once_with(1)
    uow.contact_method_repo.get_by_contact.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_methods_contact_not_found(contact_method_service, uow):
    uow.contact_repo.get = AsyncMock(return_value=None)
    uow.contact_method_repo.get_by_contact = AsyncMock()

    with pytest.raises(ContactNotFoundError, match="Contact 1 not found"):
        await contact_method_service.get_methods(
            uow,
            contact_id=1,
        )

    uow.contact_method_repo.get_by_contact.assert_not_called()


@pytest.mark.asyncio
async def test_update_method(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=1,
    )

    updated = SimpleNamespace(
        id=10,
        contact_id=1,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)
    uow.contact_method_repo.update = AsyncMock(return_value=updated)

    result = await contact_method_service.update_method(
        uow,
        contact_id=1,
        method_id=10,
        channel=ChannelType.EMAIL,
        address="new@mail.com",
        is_active=False,
    )

    assert result is updated

    uow.contact_method_repo.update.assert_called_once_with(
        10,
        channel=ChannelType.EMAIL,
        address="new@mail.com",
        is_active=False,
    )


@pytest.mark.asyncio
async def test_update_method_not_found(contact_method_service, uow):
    uow.contact_method_repo.get = AsyncMock(return_value=None)
    uow.contact_method_repo.update = AsyncMock()

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.update_method(
            uow,
            contact_id=1,
            method_id=10,
            channel=ChannelType.EMAIL,
            address="new@mail.com",
            is_active=True,
        )

    uow.contact_method_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_method_belongs_to_other_contact(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=999,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)
    uow.contact_method_repo.update = AsyncMock()

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.update_method(
            uow,
            contact_id=1,
            method_id=10,
            channel=ChannelType.EMAIL,
            address="new@mail.com",
            is_active=True,
        )

    uow.contact_method_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_delete_method(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=1,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)
    uow.contact_method_repo.delete = AsyncMock()

    await contact_method_service.delete_method(
        uow,
        contact_id=1,
        method_id=10,
    )

    uow.contact_method_repo.delete.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_delete_method_not_found(contact_method_service, uow):
    uow.contact_method_repo.get = AsyncMock(return_value=None)
    uow.contact_method_repo.delete = AsyncMock()

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.delete_method(
            uow,
            contact_id=1,
            method_id=10,
        )

    uow.contact_method_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_method_belongs_to_other_contact(contact_method_service, uow):
    method = SimpleNamespace(
        id=10,
        contact_id=999,
    )

    uow.contact_method_repo.get = AsyncMock(return_value=method)
    uow.contact_method_repo.delete = AsyncMock()

    with pytest.raises(ContactMethodNotFoundError, match="Contact method 10 not found"):
        await contact_method_service.delete_method(
            uow,
            contact_id=1,
            method_id=10,
        )

    uow.contact_method_repo.delete.assert_not_called()
