from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.fakes.fake_uow import make_mock_provider_registry, make_patched_fake_uow


@pytest.mark.asyncio
@patch("app.tasks.sweeper.send_batch_task")
@patch("app.tasks.sweeper.UnitOfWork")
@patch("app.tasks.sweeper.NotificationService")
@patch("app.tasks.sweeper.get_rate_limiter")
async def test_sweep_enqueues_batches(
    mock_get_limiter,
    mock_service_cls,
    mock_uow_cls,
    mock_send_batch_task,
):
    from app.tasks.sweeper import _sweep_deliveries

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.claim_due_retries = AsyncMock(return_value={42: [1, 2, 3]})
    service.finalize_stuck_notifications = AsyncMock(return_value=1)
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    mock_get_limiter.return_value = Mock()

    await _sweep_deliveries()

    service.claim_due_retries.assert_awaited_once_with(fake_uow)
    service.finalize_stuck_notifications.assert_awaited_once_with(fake_uow)

    mock_send_batch_task.delay.assert_called_once_with(42, [1, 2, 3])

    service.delivery_service.provider_registry.close_all.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.tasks.sweeper.send_batch_task")
@patch("app.tasks.sweeper.UnitOfWork")
@patch("app.tasks.sweeper.NotificationService")
@patch("app.tasks.sweeper.get_rate_limiter")
async def test_sweep_chunks_large_groups(
    mock_get_limiter,
    mock_service_cls,
    mock_uow_cls,
    mock_send_batch_task,
):
    from app.tasks.sweeper import _sweep_deliveries

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.claim_due_retries = AsyncMock(return_value={7: [1, 2, 3, 4, 5]})
    service.finalize_stuck_notifications = AsyncMock(return_value=0)
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    mock_get_limiter.return_value = Mock()

    with patch("app.tasks.sweeper.settings.DELIVERY_BATCH_SIZE", 2):
        await _sweep_deliveries()

    assert mock_send_batch_task.delay.call_count == 3

    mock_send_batch_task.delay.assert_any_call(7, [1, 2])
    mock_send_batch_task.delay.assert_any_call(7, [3, 4])
    mock_send_batch_task.delay.assert_any_call(7, [5])


@pytest.mark.asyncio
@patch("app.tasks.sweeper.send_batch_task")
@patch("app.tasks.sweeper.UnitOfWork")
@patch("app.tasks.sweeper.NotificationService")
@patch("app.tasks.sweeper.get_rate_limiter")
async def test_sweep_without_claims_finalizes_only(
    mock_get_limiter,
    mock_service_cls,
    mock_uow_cls,
    mock_send_batch_task,
):
    from app.tasks.sweeper import _sweep_deliveries

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.claim_due_retries = AsyncMock(return_value={})
    service.finalize_stuck_notifications = AsyncMock(return_value=2)
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    mock_get_limiter.return_value = Mock()

    await _sweep_deliveries()

    service.finalize_stuck_notifications.assert_awaited_once_with(fake_uow)

    mock_send_batch_task.delay.assert_not_called()

    service.delivery_service.provider_registry.close_all.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.tasks.sweeper.send_batch_task")
@patch("app.tasks.sweeper.UnitOfWork")
@patch("app.tasks.sweeper.NotificationService")
@patch("app.tasks.sweeper.get_rate_limiter")
async def test_sweep_closes_registry_on_error(
    mock_get_limiter,
    mock_service_cls,
    mock_uow_cls,
    mock_send_batch_task,
):
    from app.tasks.sweeper import _sweep_deliveries

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    service = Mock()
    service.claim_due_retries = AsyncMock(side_effect=RuntimeError("db down"))
    service.finalize_stuck_notifications = AsyncMock()
    service.delivery_service = Mock()
    service.delivery_service.provider_registry = make_mock_provider_registry()
    mock_service_cls.return_value = service

    mock_get_limiter.return_value = Mock()

    with pytest.raises(RuntimeError, match="db down"):
        await _sweep_deliveries()

    service.finalize_stuck_notifications.assert_not_awaited()
    mock_send_batch_task.delay.assert_not_called()

    service.delivery_service.provider_registry.close_all.assert_awaited_once()
