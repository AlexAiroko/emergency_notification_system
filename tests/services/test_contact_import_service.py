from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.contact_method import ChannelType


@pytest.mark.asyncio
@patch("app.services.contact_import.service.ContactMethodService")
@patch("app.services.contact_import.service.ContactService")
@patch("app.services.contact_import.service.ParserFactory")
async def test_import_one_transaction(mock_parser_cls, mock_contact_svc_cls, mock_method_svc_cls):
    from app.services.contact_import.service import ContactImportService

    mock_parser = Mock()
    mock_parser.parse = AsyncMock(return_value=[
        {"name": "Alice", "email": "alice@test.com"},
        {"name": "Bob", "telegram": "@bob"},
    ])
    mock_parser_cls.get.return_value = mock_parser

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock(return_value=SimpleNamespace(id=1))
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc.create_method = AsyncMock()
    mock_method_svc_cls.return_value = mock_method_svc

    uow = Mock()
    file = Mock()
    file.filename = "contacts.csv"

    service = ContactImportService()
    result = await service.import_contacts(uow=uow, file=file)

    assert result.total == 2
    assert result.imported == 2
    assert result.skipped == 0
    assert result.errors == []

    assert mock_contact_svc.create_contact.await_count == 2
    assert mock_method_svc.create_method.await_count == 2


@pytest.mark.asyncio
@patch("app.services.contact_import.service.ContactMethodService")
@patch("app.services.contact_import.service.ContactService")
@patch("app.services.contact_import.service.ParserFactory")
async def test_import_skips_empty_name(mock_parser_cls, mock_contact_svc_cls, mock_method_svc_cls):
    from app.services.contact_import.service import ContactImportService

    mock_parser = Mock()
    mock_parser.parse = AsyncMock(return_value=[
        {"name": "", "email": "test@test.com"},
    ])
    mock_parser_cls.get.return_value = mock_parser

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock()
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc_cls.return_value = mock_method_svc

    uow = Mock()
    file = Mock()
    file.filename = "contacts.csv"

    service = ContactImportService()
    result = await service.import_contacts(uow=uow, file=file)

    assert result.total == 1
    assert result.imported == 0
    assert result.skipped == 1
    assert len(result.errors) == 1
    assert result.errors[0]["row"] == 1

    mock_contact_svc.create_contact.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.contact_import.service.ContactMethodService")
@patch("app.services.contact_import.service.ContactService")
@patch("app.services.contact_import.service.ParserFactory")
async def test_import_collects_errors(mock_parser_cls, mock_contact_svc_cls, mock_method_svc_cls):
    from app.services.contact_import.service import ContactImportService

    mock_parser = Mock()
    mock_parser.parse = AsyncMock(return_value=[
        {"name": "Alice", "email": "alice@test.com"},
        {"name": ""},  # missing name -> error
        {"name": "Bob", "telegram": "@bob"},
    ])
    mock_parser_cls.get.return_value = mock_parser

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock(return_value=SimpleNamespace(id=1))
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc.create_method = AsyncMock()
    mock_method_svc_cls.return_value = mock_method_svc

    uow = Mock()
    file = Mock()
    file.filename = "contacts.csv"

    service = ContactImportService()
    result = await service.import_contacts(uow=uow, file=file)

    assert result.total == 3
    assert result.imported == 2
    assert result.skipped == 1
    assert len(result.errors) == 1
    assert result.errors[0]["row"] == 2


@pytest.mark.asyncio
@patch("app.services.contact_import.service.ContactMethodService")
@patch("app.services.contact_import.service.ContactService")
@patch("app.services.contact_import.service.ParserFactory")
async def test_import_creates_contact_with_methods(mock_parser_cls, mock_contact_svc_cls, mock_method_svc_cls):
    from app.services.contact_import.service import ContactImportService

    mock_parser = Mock()
    mock_parser.parse = AsyncMock(return_value=[
        {
            "name": "Alice",
            "external_id": "ext-1",
            "email": "alice@test.com",
            "telegram": "@alice",
        },
    ])
    mock_parser_cls.get.return_value = mock_parser

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock(return_value=SimpleNamespace(id=42))
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc.create_method = AsyncMock()
    mock_method_svc_cls.return_value = mock_method_svc

    uow = Mock()
    file = Mock()
    file.filename = "contacts.xlsx"

    service = ContactImportService()
    await service.import_contacts(uow=uow, file=file)

    mock_contact_svc.create_contact.assert_awaited_once_with(
        uow=uow,
        external_id="ext-1",
        name="Alice",
        is_active=True,
    )

    assert mock_method_svc.create_method.await_count == 2

    mock_method_svc.create_method.assert_any_await(
        uow=uow,
        contact_id=42,
        channel=ChannelType.EMAIL,
        address="alice@test.com",
    )
    mock_method_svc.create_method.assert_any_await(
        uow=uow,
        contact_id=42,
        channel=ChannelType.TELEGRAM,
        address="@alice",
    )
