from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.utils import utc_now
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
async def test_start_notification(notification_service, uow):
    uow.notification_repo.get = AsyncMock(return_value=SimpleNamespace(id=42))
    uow.notification_repo.mark_started = AsyncMock()

    await notification_service.start_notification(uow, 42)

    uow.notification_repo.get.assert_awaited_once_with(42)
    uow.notification_repo.mark_started.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_start_notification_not_found(notification_service, uow):
    uow.notification_repo.get = AsyncMock(return_value=None)

    with pytest.raises(
        NotificationNotFoundError,
        match="Notification 42 not found",
    ):
        await notification_service.start_notification(uow, 42)


@pytest.mark.asyncio
async def test_prepare_batches(notification_service, uow):
    uow.delivery_repo.get_ready_for_dispatch = AsyncMock(
        return_value=[1, 2, 3, 4, 5],
    )

    with patch("app.services.notification.settings.DELIVERY_BATCH_SIZE", 2):
        batches = await notification_service.prepare_batches(uow, 10)

    assert batches == [[1, 2], [3, 4], [5]]


@pytest.mark.asyncio
async def test_prepare_batches_empty(notification_service, uow):
    uow.delivery_repo.get_ready_for_dispatch = AsyncMock(return_value=[])

    batches = await notification_service.prepare_batches(uow, 10)

    assert batches == []


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


@pytest.mark.asyncio
async def test_claim_due_retries_groups_by_notification(notification_service, uow):
    d1 = SimpleNamespace(id=11, notification_id=100)
    d2 = SimpleNamespace(id=12, notification_id=100)
    d3 = SimpleNamespace(id=13, notification_id=200)

    uow.delivery_repo.claim_deliveries_for_retry = AsyncMock(
        return_value=[d1, d2, d3],
    )

    with patch("app.services.notification.settings.RETRY_INTERVAL_SECONDS", 30):
        before = utc_now()
        groups = await notification_service.claim_due_retries(uow)
        after = utc_now()

    assert groups == {
        100: [11, 12],
        200: [13],
    }

    uow.delivery_repo.claim_deliveries_for_retry.assert_awaited_once()

    next_attempt_at = uow.delivery_repo.claim_deliveries_for_retry.call_args.args[0]

    delta = (next_attempt_at - before).total_seconds()
    assert 29 <= delta <= 31
    assert next_attempt_at > after


@pytest.mark.asyncio
async def test_claim_due_retries_empty(notification_service, uow):
    uow.delivery_repo.claim_deliveries_for_retry = AsyncMock(return_value=[])

    groups = await notification_service.claim_due_retries(uow)

    assert groups == {}


@pytest.mark.asyncio
async def test_finalize_stuck_notifications_finalizes_each(notification_service, uow):
    uow.notification_repo.get_stuck_in_progress_ids = AsyncMock(
        return_value=[1, 2],
    )
    uow.delivery_repo.get_stats = AsyncMock(return_value={"sent": 1})
    uow.notification_repo.update_status = AsyncMock()

    count = await notification_service.finalize_stuck_notifications(uow)

    assert count == 2

    uow.notification_repo.get_stuck_in_progress_ids.assert_awaited_once()
    uow.delivery_repo.get_stats.assert_awaited_with(2)
    assert uow.delivery_repo.get_stats.await_count == 2
    assert uow.notification_repo.update_status.await_count == 2


@pytest.mark.asyncio
async def test_finalize_stuck_notifications_empty(notification_service, uow):
    uow.notification_repo.get_stuck_in_progress_ids = AsyncMock(return_value=[])

    count = await notification_service.finalize_stuck_notifications(uow)

    assert count == 0

    uow.delivery_repo.get_stats.assert_not_called()
    uow.notification_repo.update_status.assert_not_called()
