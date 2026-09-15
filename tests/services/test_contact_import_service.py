from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.exceptions.contact_import import (
    FileTooLargeError,
    ImportJobNotFoundError,
    UnsupportedImportFileError,
)


@pytest.mark.asyncio
async def test_start_import():
    from app.services.contact_import.service import ContactImportService

    job = SimpleNamespace(id=1, filename="contacts.csv")

    mock_uow = Mock()
    mock_uow.import_job_repo = Mock()
    mock_uow.import_job_repo.create = AsyncMock(return_value=job)
    mock_uow.commit = AsyncMock()

    mock_file = Mock()
    mock_file.filename = "contacts.csv"
    mock_file.read = AsyncMock(return_value=b"file content")

    with patch("app.services.contact_import.service.get_s3_client") as mock_s3_cls, \
         patch("app.services.contact_import.service.import_contacts_task") as mock_task:
        mock_s3 = Mock()
        mock_s3_cls.return_value = mock_s3

        service = ContactImportService()
        result = await service.start_import(mock_uow, mock_file)

        assert result is job
        mock_uow.import_job_repo.create.assert_awaited_once_with(filename="contacts.csv")
        mock_uow.commit.assert_awaited()
        mock_s3.upload.assert_called_once_with("imports/1/contacts.csv", b"file content")
        mock_task.delay.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_start_import_no_filename():
    from app.services.contact_import.service import ContactImportService

    mock_uow = Mock()
    mock_file = Mock()
    mock_file.filename = None

    service = ContactImportService()

    with pytest.raises(UnsupportedImportFileError):
        await service.start_import(mock_uow, mock_file)


@pytest.mark.asyncio
async def test_start_import_unsupported_ext():
    from app.services.contact_import.service import ContactImportService

    mock_uow = Mock()
    mock_file = Mock()
    mock_file.filename = "data.json"

    service = ContactImportService()

    with pytest.raises(UnsupportedImportFileError):
        await service.start_import(mock_uow, mock_file)


@pytest.mark.asyncio
async def test_get_import_status():
    from app.services.contact_import.service import ContactImportService

    job = SimpleNamespace(id=1)

    mock_uow = Mock()
    mock_uow.import_job_repo = Mock()
    mock_uow.import_job_repo.get = AsyncMock(return_value=job)

    service = ContactImportService()
    result = await service.get_import_status(mock_uow, 1)

    assert result is job
    mock_uow.import_job_repo.get.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_import_status_not_found():
    from app.services.contact_import.service import ContactImportService

    mock_uow = Mock()
    mock_uow.import_job_repo = Mock()
    mock_uow.import_job_repo.get = AsyncMock(return_value=None)

    service = ContactImportService()

    with pytest.raises(ImportJobNotFoundError):
        await service.get_import_status(mock_uow, 999)


@pytest.mark.asyncio
async def test_start_import_file_too_large():
    from app.services.contact_import.service import ContactImportService

    mock_uow = Mock()
    mock_file = Mock()
    mock_file.filename = "contacts.csv"
    mock_file.read = AsyncMock(return_value=b"x" * 11)

    with patch("app.services.contact_import.service.settings") as mock_settings:
        mock_settings.MAX_FILE_SIZE_BYTES = 10

        service = ContactImportService()

        with pytest.raises(FileTooLargeError):
            await service.start_import(mock_uow, mock_file)
