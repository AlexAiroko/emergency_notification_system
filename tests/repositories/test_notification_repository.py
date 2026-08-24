from datetime import timedelta

import pytest

from app.core.utils import utc_now
from app.models.delivery import DeliveryStatus
from app.models.notification import NotificationStatus


@pytest.mark.asyncio
async def test_create_notification(notification_template, group, notification_repo):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    assert notification.id is not None
    assert notification.template_id == notification_template.id
    assert notification.group_id == group.id
    assert notification.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_get_notification(notification_template, group, notification_repo):
    created = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    found = await notification_repo.get(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.template_id == notification_template.id


@pytest.mark.asyncio
async def test_get_notification_not_found(notification_repo):
    result = await notification_repo.get(999999)

    assert result is None


@pytest.mark.asyncio
async def test_get_with_relations(notification_template, group, notification_repo):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    result = await notification_repo.get_with_relations(notification.id)

    assert result is not None
    assert result.template is not None
    assert result.group is not None
    assert result.template.id == notification_template.id
    assert result.group.id == group.id


@pytest.mark.asyncio
async def test_get_with_relations_not_found(notification_repo):
    result = await notification_repo.get_with_relations(999999)

    assert result is None


@pytest.mark.asyncio
async def test_mark_started_without_commit(notification_template, group, notification_repo):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    await notification_repo.mark_started(notification.id)

    updated = await notification_repo.get(notification.id)
    assert updated.status == NotificationStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_mark_finished(notification_template, group, notification_repo):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    await notification_repo.mark_finished(notification.id)

    updated = await notification_repo.get(notification.id)

    assert updated.status == NotificationStatus.SUCCESS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        NotificationStatus.PENDING,
        NotificationStatus.IN_PROGRESS,
        NotificationStatus.SUCCESS,
        NotificationStatus.FAILED,
    ],
)
async def test_update_status_direct(
    notification_template,
    group,
    status,
    notification_repo,
):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    await notification_repo.update_status(notification.id, status)

    updated = await notification_repo.get(notification.id)

    assert updated.status == status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    [
        "mark_started",
        "mark_finished",
    ],
)
async def test_mark_started_non_existing(method_name, notification_repo):
    # Method shouldn't throw an exception
    await getattr(notification_repo, method_name)(999999)


@pytest.mark.asyncio
async def test_get_stuck_in_progress_ids_includes_without_deliveries(
    notification_template,
    group,
    notification_repo,
):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    await notification_repo.mark_started(notification.id)

    stuck = await notification_repo.get_stuck_in_progress_ids()

    assert stuck == [notification.id]


@pytest.mark.asyncio
async def test_get_stuck_in_progress_ids_excludes_with_pending_delivery(
    delivery_factory,
    notification,
    contact,
    contact_method,
    notification_repo,
):
    await notification_repo.mark_started(notification.id)

    await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        status=DeliveryStatus.PENDING,
    )

    stuck = await notification_repo.get_stuck_in_progress_ids()

    assert stuck == []


@pytest.mark.asyncio
async def test_get_stuck_in_progress_ids_excludes_future_pending_delivery(
    delivery_factory,
    notification,
    contact,
    contact_method,
    notification_repo,
):
    await notification_repo.mark_started(notification.id)

    await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        status=DeliveryStatus.PENDING,
        next_attempt_at=utc_now() + timedelta(minutes=5),
    )

    stuck = await notification_repo.get_stuck_in_progress_ids()

    assert stuck == []


@pytest.mark.asyncio
async def test_get_stuck_in_progress_ids_includes_with_terminal_deliveries(
    delivery_factory,
    notification,
    contact,
    contact_method,
    notification_repo,
):
    await notification_repo.mark_started(notification.id)

    await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        status=DeliveryStatus.SENT,
    )

    await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        status=DeliveryStatus.FAILED,
    )

    stuck = await notification_repo.get_stuck_in_progress_ids()

    assert stuck == [notification.id]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        NotificationStatus.PENDING,
        NotificationStatus.SUCCESS,
        NotificationStatus.FAILED,
    ],
)
async def test_get_stuck_in_progress_ids_excludes_other_statuses(
    notification_template,
    group,
    status,
    notification_repo,
):
    notification = await notification_repo.create(
        template_id=notification_template.id,
        group_id=group.id,
    )

    await notification_repo.update_status(notification.id, status)

    stuck = await notification_repo.get_stuck_in_progress_ids()

    assert stuck == []
