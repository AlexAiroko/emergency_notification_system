from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions.delivery import DeliveryNotFoundError
from app.exceptions.notification import NotificationNotFoundError
from app.models.contact_method import ChannelType
from app.models.delivery import DeliveryStatus
from app.providers.base import ProviderError


@pytest.mark.asyncio
async def test_send_success(delivery_service, uow):
    delivery = SimpleNamespace(
        id=1,
        notification_id=10,
        channel=ChannelType.EMAIL,
        address="user@mail.com",
        attempts=0,
    )

    notification = SimpleNamespace(
        template_id=100,
    )

    template = SimpleNamespace(
        subject="Subject",
        body="Body",
    )

    provider = Mock()
    provider.send = AsyncMock(return_value="msg-123")

    uow.delivery_repo.get = AsyncMock(return_value=delivery)
    uow.notification_repo.get_with_relations = AsyncMock(return_value=notification)
    uow.delivery_repo.mark_sent = AsyncMock()
    uow.delivery_repo.mark_failed = AsyncMock()

    delivery_service.template_service.ensure_template_is_active = AsyncMock(
        return_value=template,
    )
    delivery_service.provider_registry.get = Mock(return_value=provider)

    await delivery_service.send_delivery(uow, 1)

    delivery_service.template_service.ensure_template_is_active.assert_awaited_once_with(
        uow,
        100,
    )

    provider.send.assert_awaited_once_with(
        to="user@mail.com",
        subject="Subject",
        body="Body",
    )

    uow.delivery_repo.mark_sent.assert_awaited_once_with(
        1,
        provider_message_id="msg-123",
    )

    uow.delivery_repo.mark_failed.assert_not_called()


@pytest.mark.asyncio
async def test_send_delivery_not_found(delivery_service, uow):
    uow.delivery_repo.get = AsyncMock(return_value=None)
    uow.notification_repo.get_with_relations = AsyncMock()

    with pytest.raises(
        DeliveryNotFoundError,
        match="Delivery 1 not found",
    ):
        await delivery_service.send_delivery(uow, 1)

    uow.notification_repo.get_with_relations.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_not_found(delivery_service, uow):
    delivery = SimpleNamespace(
        id=1,
        notification_id=10,
    )

    uow.delivery_repo.get = AsyncMock(return_value=delivery)
    uow.notification_repo.get_with_relations = AsyncMock(return_value=None)

    with pytest.raises(
        NotificationNotFoundError,
        match="Notification 10 not found",
    ):
        await delivery_service.send_delivery(uow, 1)


@pytest.mark.asyncio
async def test_send_provider_error(delivery_service, uow):
    delivery = SimpleNamespace(
        id=1,
        notification_id=10,
        channel=ChannelType.EMAIL,
        address="user@mail.com",
        attempts=0,
    )

    notification = SimpleNamespace(
        template_id=100,
    )

    template = SimpleNamespace(
        subject="Subject",
        body="Body",
    )

    provider = Mock()
    provider.send = AsyncMock(
        side_effect=ProviderError("SMTP failed"),
    )

    uow.delivery_repo.get = AsyncMock(return_value=delivery)
    uow.notification_repo.get_with_relations = AsyncMock(return_value=notification)
    uow.delivery_repo.mark_sent = AsyncMock()
    uow.delivery_repo.mark_failed = AsyncMock()
    uow.delivery_repo.mark_retry = AsyncMock()

    delivery_service.template_service.ensure_template_is_active = AsyncMock(
        return_value=template,
    )
    delivery_service.provider_registry.get = Mock(return_value=provider)

    await delivery_service.send_delivery(uow, 1)

    uow.delivery_repo.mark_retry.assert_awaited_once()
    assert uow.delivery_repo.mark_retry.call_args.kwargs["error_message"] == "SMTP failed"

    uow.delivery_repo.mark_failed.assert_not_called()
    uow.delivery_repo.mark_sent.assert_not_called()


@pytest.mark.asyncio
async def test_send_provider_error_retries_exhausted(delivery_service, uow):
    delivery = SimpleNamespace(
        id=1,
        notification_id=10,
        channel=ChannelType.EMAIL,
        address="user@mail.com",
        attempts=5,
    )

    notification = SimpleNamespace(
        template_id=100,
    )

    template = SimpleNamespace(
        subject="Subject",
        body="Body",
    )

    provider = Mock()
    provider.send = AsyncMock(
        side_effect=ProviderError("SMTP failed"),
    )

    uow.delivery_repo.get = AsyncMock(return_value=delivery)
    uow.notification_repo.get_with_relations = AsyncMock(return_value=notification)
    uow.delivery_repo.mark_sent = AsyncMock()
    uow.delivery_repo.mark_failed = AsyncMock()
    uow.delivery_repo.mark_retry = AsyncMock()

    delivery_service.template_service.ensure_template_is_active = AsyncMock(
        return_value=template,
    )
    delivery_service.provider_registry.get = Mock(return_value=provider)

    await delivery_service.send_delivery(uow, 1)

    uow.delivery_repo.mark_failed.assert_awaited_once_with(
        1,
        error_message="SMTP failed",
    )

    uow.delivery_repo.mark_retry.assert_not_called()
    uow.delivery_repo.mark_sent.assert_not_called()


@pytest.mark.asyncio
async def test_send_pending(delivery_service, uow):
    d1 = SimpleNamespace(
        id=1,
        status=DeliveryStatus.PENDING,
    )

    d2 = SimpleNamespace(
        id=2,
        status=DeliveryStatus.SENT,
    )

    d3 = SimpleNamespace(
        id=3,
        status=DeliveryStatus.PENDING,
    )

    uow.delivery_repo.get_by_notification = AsyncMock(
        return_value=[d1, d2, d3],
    )

    delivery_service.send_delivery = AsyncMock()

    await delivery_service.send_pending(
        uow,
        notification_id=10,
    )

    delivery_service.send_delivery.assert_any_await(
        uow,
        1,
    )

    delivery_service.send_delivery.assert_any_await(
        uow,
        3,
    )

    assert delivery_service.send_delivery.await_count == 2
