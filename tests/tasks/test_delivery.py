from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.fakes.fake_uow import make_mock_provider_registry, make_patched_fake_uow


@pytest.mark.asyncio
@patch("app.tasks.delivery.UnitOfWork")
@patch("app.tasks.delivery.DeliveryService")
@patch("app.tasks.delivery.NotificationService")
@patch("app.tasks.delivery.RateLimiter")
async def test_send_batch_happy_path(
    mock_rate_limiter_cls,
    mock_notification_svc_cls,
    mock_delivery_svc_cls,
    mock_uow_cls,
):
    from app.tasks.delivery import _send_batch

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    delivery_svc = Mock()
    delivery_svc.send_deliveries = AsyncMock()
    delivery_svc.provider_registry = make_mock_provider_registry()
    mock_delivery_svc_cls.return_value = delivery_svc

    notification_svc = Mock()
    notification_svc.finalize_notification = AsyncMock()
    mock_notification_svc_cls.return_value = notification_svc

    mock_limiter = AsyncMock()
    mock_rate_limiter_cls.return_value = mock_limiter

    await _send_batch(42, [10, 20, 30])

    delivery_svc.send_deliveries.assert_awaited_once_with(fake_uow, [10, 20, 30])
    notification_svc.finalize_notification.assert_awaited_once_with(fake_uow, 42)
    delivery_svc.provider_registry.close_all.assert_awaited_once()

    mock_rate_limiter_cls.assert_called_once()
    mock_limiter.__aenter__.assert_awaited_once()
    mock_limiter.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.tasks.delivery.UnitOfWork")
@patch("app.tasks.delivery.DeliveryService")
@patch("app.tasks.delivery.NotificationService")
@patch("app.tasks.delivery.RateLimiter")
async def test_send_batch_closes_on_exception(
    mock_rate_limiter_cls,
    mock_notification_svc_cls,
    mock_delivery_svc_cls,
    mock_uow_cls,
):
    from app.tasks.delivery import _send_batch

    fake_uow = make_patched_fake_uow()
    mock_uow_cls.return_value = fake_uow

    delivery_svc = Mock()
    delivery_svc.send_deliveries = AsyncMock(side_effect=RuntimeError("db down"))
    delivery_svc.provider_registry = make_mock_provider_registry()
    mock_delivery_svc_cls.return_value = delivery_svc

    notification_svc = Mock()
    notification_svc.finalize_notification = AsyncMock()
    mock_notification_svc_cls.return_value = notification_svc

    mock_limiter = AsyncMock()
    mock_rate_limiter_cls.return_value = mock_limiter

    with pytest.raises(RuntimeError, match="db down"):
        await _send_batch(42, [10])

    delivery_svc.provider_registry.close_all.assert_awaited_once()
    notification_svc.finalize_notification.assert_not_awaited()
    mock_limiter.__aexit__.assert_awaited_once()
