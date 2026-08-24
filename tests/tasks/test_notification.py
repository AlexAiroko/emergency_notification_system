from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.fakes.fake_uow import make_mock_provider_registry, make_patched_fake_uow


@pytest.mark.asyncio
@patch("app.tasks.notification.send_batch_task")
@patch("app.tasks.notification.UnitOfWork")
@patch("app.tasks.notification.NotificationService")
async def test_dispatch_notification_enqueues_batches(
    mock_service_cls,
    mock_uow_cls,
    mock_send_batch_task,
):
    # Import inside test body: @patch replaces the module before it is loaded.
    from app.tasks.notification import _dispatch_notification

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.start_notification = AsyncMock()
    service.prepare_batches = AsyncMock(return_value=[[1, 2], [3]])
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    await _dispatch_notification(42)

    service.start_notification.assert_awaited_once_with(
        uow=fake_uow, notification_id=42,
    )
    service.prepare_batches.assert_awaited_once_with(fake_uow, 42)

    assert mock_send_batch_task.delay.call_count == 2
    mock_send_batch_task.delay.assert_any_call(42, [1, 2])
    mock_send_batch_task.delay.assert_any_call(42, [3])

    service.delivery_service.provider_registry.close_all.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.tasks.notification.UnitOfWork")
@patch("app.tasks.notification.NotificationService")
async def test_dispatch_notification_no_batches_finalizes(
    mock_service_cls,
    mock_uow_cls,
):
    from app.tasks.notification import _dispatch_notification

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.start_notification = AsyncMock()
    service.prepare_batches = AsyncMock(return_value=[])
    service.finalize_notification = AsyncMock()
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    await _dispatch_notification(42)

    assert mock_uow_cls.call_count == 2
    service.finalize_notification.assert_awaited_once_with(fake_uow, 42)
    service.delivery_service.provider_registry.close_all.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.tasks.notification.UnitOfWork")
@patch("app.tasks.notification.NotificationService")
async def test_dispatch_notification_start_error_still_closes(
    mock_service_cls,
    mock_uow_cls,
):
    from app.exceptions.notification import NotificationNotFoundError
    from app.tasks.notification import _dispatch_notification

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.start_notification = AsyncMock(
        side_effect=NotificationNotFoundError(42),
    )
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    with pytest.raises(NotificationNotFoundError):
        await _dispatch_notification(42)

    service.delivery_service.provider_registry.close_all.assert_awaited_once()
