from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.exceptions.notification import NotificationNotFoundError
from app.models.contact_method import ChannelType
from app.models.delivery import DeliveryStatus
from app.models.notification import NotificationStatus


@pytest.mark.asyncio
async def test_create_notification(notification_service, uow):
    notification = SimpleNamespace(id=1)

    email = SimpleNamespace(
        id=10,
        channel=ChannelType.EMAIL,
        address="user@example.com",
    )

    telegram = SimpleNamespace(
        id=11,
        channel=ChannelType.TELEGRAM,
        address="123456789",
    )

    contact = SimpleNamespace(
        id=100,
        contact_methods=[email, telegram],
    )

    uow.group_repo.get_with_contacts = AsyncMock(return_value=SimpleNamespace(id=7))
    uow.notification_repo.create = AsyncMock(return_value=notification)
    uow.group_repo.get_contacts_for_dispatch = AsyncMock(return_value=[contact])
    uow.delivery_repo.create_bulk = AsyncMock()

    notification_service.template_service.ensure_template_is_active = AsyncMock()

    result = await notification_service.create_notification(
        uow,
        template_id=5,
        group_id=7,
    )

    assert result is notification

    notification_service.template_service.ensure_template_is_active.assert_awaited_once_with(
        uow,
        5,
    )

    uow.group_repo.get_with_contacts.assert_awaited_once_with(7)

    uow.notification_repo.create.assert_awaited_once_with(
        template_id=5,
        group_id=7,
    )

    uow.group_repo.get_contacts_for_dispatch.assert_awaited_once_with(7)

    uow.delivery_repo.create_bulk.assert_awaited_once()

    deliveries = uow.delivery_repo.create_bulk.call_args.args[0]

    assert len(deliveries) == 2

    assert deliveries[0].notification_id == 1
    assert deliveries[0].contact_id == 100
    assert deliveries[0].contact_method_id == 10
    assert deliveries[0].channel == ChannelType.EMAIL
    assert deliveries[0].address == "user@example.com"
    assert deliveries[0].status == DeliveryStatus.PENDING

    assert deliveries[1].contact_method_id == 11
    assert deliveries[1].channel == ChannelType.TELEGRAM
    assert deliveries[1].address == "123456789"


@pytest.mark.asyncio
async def test_create_notification_without_contacts(notification_service, uow):
    notification = SimpleNamespace(id=1)

    uow.group_repo.get_with_contacts = AsyncMock(return_value=SimpleNamespace(id=1))
    uow.notification_repo.create = AsyncMock(return_value=notification)
    uow.group_repo.get_contacts_for_dispatch = AsyncMock(return_value=[])
    uow.delivery_repo.create_bulk = AsyncMock()

    notification_service.template_service.ensure_template_is_active = AsyncMock()

    result = await notification_service.create_notification(
        uow,
        template_id=1,
        group_id=1,
    )

    assert result is notification

    uow.delivery_repo.create_bulk.assert_not_called()


@pytest.mark.asyncio
async def test_create_notification_with_contact_without_methods(notification_service, uow):
    notification = SimpleNamespace(id=1)

    contact = SimpleNamespace(
        id=100,
        contact_methods=[],
    )

    uow.group_repo.get_with_contacts = AsyncMock(return_value=SimpleNamespace(id=1))
    uow.notification_repo.create = AsyncMock(return_value=notification)
    uow.group_repo.get_contacts_for_dispatch = AsyncMock(return_value=[contact])
    uow.delivery_repo.create_bulk = AsyncMock()

    notification_service.template_service.ensure_template_is_active = AsyncMock()

    await notification_service.create_notification(
        uow,
        template_id=1,
        group_id=1,
    )

    uow.delivery_repo.create_bulk.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification(notification_service, uow):
    uow.notification_repo.get = AsyncMock(return_value=SimpleNamespace(id=42))
    uow.notification_repo.mark_started = AsyncMock()

    notification_service.delivery_service.send_pending = AsyncMock()
    notification_service.finalize_notification = AsyncMock()

    await notification_service.send_notification(
        uow,
        42,
    )

    uow.notification_repo.mark_started.assert_awaited_once_with(42)

    notification_service.delivery_service.send_pending.assert_awaited_once_with(
        uow,
        42,
    )

    notification_service.finalize_notification.assert_awaited_once_with(
        uow,
        42,
    )


@pytest.mark.asyncio
async def test_send_notification_not_found(notification_service, uow):
    uow.notification_repo.get = AsyncMock(return_value=None)

    with pytest.raises(
        NotificationNotFoundError,
        match="Notification 42 not found",
    ):
        await notification_service.send_notification(
            uow,
            42,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stats", "expected_status"),
    [
        ({"sent": 3}, NotificationStatus.SUCCESS),
        ({"failed": 3}, NotificationStatus.FAILED),
        ({"sent": 2, "failed": 1}, NotificationStatus.PARTIAL_SUCCESS),
        ({"sent": 1, "failed": 1}, NotificationStatus.PARTIAL_SUCCESS),
        ({"sent": 3, "pending": 0}, NotificationStatus.SUCCESS),
    ],
)
async def test_finalize_notification(
    notification_service,
    uow,
    stats,
    expected_status,
):
    uow.delivery_repo.get_stats = AsyncMock(return_value=stats)
    uow.notification_repo.update_status = AsyncMock()

    await notification_service.finalize_notification(
        uow,
        1,
    )

    uow.delivery_repo.get_stats.assert_awaited_once_with(1)

    uow.notification_repo.update_status.assert_awaited_once_with(
        1,
        expected_status,
    )


@pytest.mark.asyncio
async def test_finalize_notification_no_deliveries_marks_success(notification_service, uow):
    uow.delivery_repo.get_stats = AsyncMock(return_value={})
    uow.notification_repo.update_status = AsyncMock()

    await notification_service.finalize_notification(
        uow,
        1,
    )

    uow.delivery_repo.get_stats.assert_awaited_once_with(1)

    uow.notification_repo.update_status.assert_awaited_once_with(
        1,
        NotificationStatus.SUCCESS,
    )


@pytest.mark.asyncio
async def test_finalize_notification_skips_when_pending_deliveries(notification_service, uow):
    uow.delivery_repo.get_stats = AsyncMock(return_value={"sent": 1, "pending": 2})
    uow.notification_repo.update_status = AsyncMock()

    await notification_service.finalize_notification(uow, 1)

    uow.notification_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_finalize_notification_skips_when_only_pending(notification_service, uow):
    uow.delivery_repo.get_stats = AsyncMock(return_value={"pending": 3})
    uow.notification_repo.update_status = AsyncMock()

    await notification_service.finalize_notification(uow, 1)

    uow.notification_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_create_notification_propagates_template_validation_error(
    notification_service,
    uow,
):
    notification_service.template_service.ensure_template_is_active = AsyncMock(
        side_effect=ValueError("Template is inactive"),
    )

    with pytest.raises(
        ValueError,
        match="Template is inactive",
    ):
        await notification_service.create_notification(
            uow,
            template_id=1,
            group_id=1,
        )

    uow.notification_repo.create.assert_not_called()
    uow.group_repo.get_contacts_for_dispatch.assert_not_called()
    uow.delivery_repo.create_bulk.assert_not_called()
