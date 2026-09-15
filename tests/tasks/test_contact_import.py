from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.fakes.fake_uow import make_patched_fake_uow


def _make_csv_bytes(rows: list[dict]) -> bytes:
    import csv
    import io

    if not rows:
        return b"external_id,name,email,telegram,phone\n"

    headers = list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


@pytest.mark.asyncio
@patch("app.tasks.contact_import.UnitOfWork")
@patch("app.tasks.contact_import.ContactMethodService")
@patch("app.tasks.contact_import.ContactService")
@patch("app.tasks.contact_import.get_s3_client")
@patch("app.tasks.contact_import.settings")
async def test_process_import_happy_path(
    mock_settings,
    mock_s3_cls,
    mock_contact_svc_cls,
    mock_method_svc_cls,
    mock_uow_cls,
):
    from app.tasks.contact_import import _process_import

    mock_settings.IMPORT_BATCH_SIZE = 100
    mock_settings.IMPORT_DIR = "imports"
    mock_settings.S3_RETRY_COUNT = 3

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    job = SimpleNamespace(id=1, filename="contacts.csv")
    fake_uow.import_job_repo.get = AsyncMock(return_value=job)
    fake_uow.import_job_repo.update_progress = AsyncMock()
    fake_uow.import_job_repo.mark_completed = AsyncMock()

    csv_bytes = _make_csv_bytes([
        {"external_id": "ext-1", "name": "Alice", "email": "alice@test.com", "telegram": "@alice", "phone": ""},
        {"external_id": "ext-2", "name": "Bob", "email": "", "telegram": "@bob", "phone": "+123456"},
    ])

    mock_s3 = Mock()
    mock_s3.download.return_value = csv_bytes
    mock_s3_cls.return_value = mock_s3

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock(return_value=SimpleNamespace(id=10))
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc.create_method = AsyncMock()
    mock_method_svc_cls.return_value = mock_method_svc

    await _process_import(1)

    mock_s3.download.assert_called_once_with("imports/1/contacts.csv")
    assert mock_contact_svc.create_contact.await_count == 2
    assert mock_method_svc.create_method.await_count == 4
    fake_uow.import_job_repo.mark_completed.assert_awaited_once_with(1)
    mock_s3.delete.assert_called_once_with("imports/1/contacts.csv")


@pytest.mark.asyncio
@patch("app.tasks.contact_import.UnitOfWork")
@patch("app.tasks.contact_import.ContactMethodService")
@patch("app.tasks.contact_import.ContactService")
@patch("app.tasks.contact_import.get_s3_client")
@patch("app.tasks.contact_import.settings")
async def test_process_import_row_failure(
    mock_settings,
    mock_s3_cls,
    mock_contact_svc_cls,
    mock_method_svc_cls,
    mock_uow_cls,
):
    from app.tasks.contact_import import _process_import

    mock_settings.IMPORT_BATCH_SIZE = 100
    mock_settings.IMPORT_DIR = "imports"
    mock_settings.S3_RETRY_COUNT = 3

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    job = SimpleNamespace(id=1, filename="contacts.csv")
    fake_uow.import_job_repo.get = AsyncMock(return_value=job)
    fake_uow.import_job_repo.update_progress = AsyncMock()
    fake_uow.import_job_repo.mark_completed = AsyncMock()

    csv_bytes = _make_csv_bytes([
        {"external_id": "ext-1", "name": "Alice", "email": "alice@test.com", "telegram": "@alice", "phone": ""},
        {"external_id": "", "name": "", "email": "", "telegram": "", "phone": ""},
    ])

    mock_s3 = Mock()
    mock_s3.download.return_value = csv_bytes
    mock_s3_cls.return_value = mock_s3

    mock_contact_svc = Mock()
    mock_contact_svc.create_contact = AsyncMock(return_value=SimpleNamespace(id=10))
    mock_contact_svc_cls.return_value = mock_contact_svc

    mock_method_svc = Mock()
    mock_method_svc.create_method = AsyncMock()
    mock_method_svc_cls.return_value = mock_method_svc

    await _process_import(1)

    assert mock_contact_svc.create_contact.await_count == 1
    fake_uow.import_job_repo.mark_completed.assert_awaited_once_with(1)
    mock_s3.delete.assert_called_once()


@pytest.mark.asyncio
@patch("app.tasks.contact_import.UnitOfWork")
@patch("app.tasks.contact_import.ContactMethodService")
@patch("app.tasks.contact_import.ContactService")
@patch("app.tasks.contact_import.get_s3_client")
async def test_process_import_job_not_found(
    mock_s3_cls,
    mock_contact_svc_cls,
    mock_method_svc_cls,
    mock_uow_cls,
):
    from app.tasks.contact_import import _process_import

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    fake_uow.import_job_repo.get = AsyncMock(return_value=None)

    mock_s3 = Mock()
    mock_s3_cls.return_value = mock_s3

    await _process_import(999)

    mock_s3.download.assert_not_called()
    mock_s3.delete.assert_not_called()


@pytest.mark.asyncio
@patch("app.tasks.contact_import.UnitOfWork")
@patch("app.tasks.contact_import.ContactMethodService")
@patch("app.tasks.contact_import.ContactService")
@patch("app.tasks.contact_import.get_s3_client")
@patch("app.tasks.contact_import.settings")
async def test_process_import_cleanup_on_error(
    mock_settings,
    mock_s3_cls,
    mock_contact_svc_cls,
    mock_method_svc_cls,
    mock_uow_cls,
):
    from app.tasks.contact_import import _process_import

    mock_settings.IMPORT_BATCH_SIZE = 100
    mock_settings.IMPORT_DIR = "imports"

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    job = SimpleNamespace(id=1, filename="contacts.csv")
    fake_uow.import_job_repo.get = AsyncMock(return_value=job)
    fake_uow.import_job_repo.mark_failed = AsyncMock()

    mock_s3 = Mock()
    mock_s3.download.side_effect = RuntimeError("S3 down")
    mock_s3_cls.return_value = mock_s3

    await _process_import(1)

    fake_uow.import_job_repo.mark_failed.assert_awaited_once()
    mock_s3.delete.assert_called_once_with("imports/1/contacts.csv")


@pytest.mark.asyncio
@patch("app.tasks.contact_import.UnitOfWork")
@patch("app.tasks.contact_import.ContactMethodService")
@patch("app.tasks.contact_import.ContactService")
@patch("app.tasks.contact_import.get_s3_client")
@patch("app.tasks.contact_import.settings")
async def test_process_import_s3_retries_on_connection_error(
    mock_settings,
    mock_s3_cls,
    mock_contact_svc_cls,
    mock_method_svc_cls,
    mock_uow_cls,
):
    from app.tasks.contact_import import _process_import

    mock_settings.IMPORT_BATCH_SIZE = 100
    mock_settings.IMPORT_DIR = "imports"
    mock_settings.S3_RETRY_COUNT = 3

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    job = SimpleNamespace(id=1, filename="contacts.csv")
    fake_uow.import_job_repo.get = AsyncMock(return_value=job)
    fake_uow.import_job_repo.mark_failed = AsyncMock()

    mock_s3 = Mock()
    mock_s3.download.side_effect = ConnectionError("MinIO unavailable")
    mock_s3_cls.return_value = mock_s3

    await _process_import(1)

    assert mock_s3.download.call_count == 3
    fake_uow.import_job_repo.mark_failed.assert_awaited_once()
    mock_s3.delete.assert_called_once_with("imports/1/contacts.csv")
