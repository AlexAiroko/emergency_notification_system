from datetime import datetime, timedelta, timezone

import pytest

from app.models.delivery import Delivery, DeliveryStatus


@pytest.mark.asyncio
async def test_create_delivery(notification, contact, contact_method, delivery_repo):
    delivery = await delivery_repo.create(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        channel="email",
        address="a@a.com",
    )

    assert delivery.id is not None
    assert delivery.status == DeliveryStatus.PENDING
    assert delivery.address == "a@a.com"
    assert delivery.notification_id == notification.id
    assert delivery.contact_id == contact.id
    assert delivery.contact_method_id == contact_method.id


@pytest.mark.asyncio
async def test_create_bulk(
    notification,
    contact,
    contact_method,
    second_contact_with_method,
    delivery_repo,
):
    contact2, contact_method2 = second_contact_with_method

    d1 = Delivery(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        channel="email",
        address="a@a.com",
    )

    d2 = Delivery(
        notification_id=notification.id,
        contact_id=contact2.id,
        contact_method_id=contact_method2.id,
        channel="sms",
        address="+111",
    )

    await delivery_repo.create_bulk([d1, d2])

    res = await delivery_repo.get_by_notification(notification.id)

    assert len(res) == 2


@pytest.mark.asyncio
async def test_get_delivery(
    delivery_factory,
    notification,
    contact,
    contact_method,
    delivery_repo,
):
    created = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    found = await delivery_repo.get(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.notification_id == created.notification_id
    assert found.contact_id == created.contact_id
    assert found.contact_method_id == created.contact_method_id


@pytest.mark.asyncio
async def test_get_delivery_not_found(delivery_repo):
    result = await delivery_repo.get(999999)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("count", [0, 1, 5])
async def test_get_by_notification(
    delivery_factory,
    notification,
    contact,
    contact_method,
    count,
    delivery_repo,
):
    for _ in range(count):
        await delivery_factory(
            notification_id=notification.id,
            contact_id=contact.id,
            contact_method_id=contact_method.id,
        )

    res = await delivery_repo.get_by_notification(notification.id)

    assert len(res) == count


@pytest.mark.asyncio
async def test_update_status(
    delivery_factory,
    notification,
    contact,
    contact_method,
    delivery_repo,
):
    delivery = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    await delivery_repo.update_status(delivery.id, DeliveryStatus.SENT)

    updated = (await delivery_repo.get_by_notification(notification.id))[0]

    assert updated.status == DeliveryStatus.SENT


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_id", [None, "msg-123"])
async def test_mark_sent(
    delivery_factory,
    notification,
    contact,
    contact_method,
    provider_id,
    delivery_repo,
):
    delivery = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    await delivery_repo.mark_sent(delivery.id, provider_id)

    updated = (await delivery_repo.get_by_notification(notification.id))[0]

    assert updated.status == DeliveryStatus.SENT
    assert updated.provider_message_id == provider_id


@pytest.mark.asyncio
async def test_mark_failed(
    delivery_factory,
    notification,
    contact,
    contact_method,
    delivery_repo,
):
    delivery = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    await delivery_repo.mark_failed(delivery.id, "network error")

    updated = (await delivery_repo.get_by_notification(notification.id))[0]

    assert updated.status == DeliveryStatus.FAILED
    assert updated.error_message == "network error"


@pytest.mark.asyncio
async def test_get_stats(
    delivery_factory,
    notification,
    contact,
    contact_method,
    extra_contacts,
    delivery_repo,
):
    (c2, cm2), (c3, cm3) = extra_contacts

    await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
        status=DeliveryStatus.SENT,
    )
    
    await delivery_factory(
        notification_id=notification.id,
        contact_id=c2.id,
        contact_method_id=cm2.id,
        status=DeliveryStatus.SENT,
    )
    
    await delivery_factory(
        notification_id=notification.id,
        contact_id=c3.id,
        contact_method_id=cm3.id,
        status=DeliveryStatus.FAILED,
    )

    stats = await delivery_repo.get_stats(notification.id)

    assert stats["sent"] == 2
    assert stats["failed"] == 1


@pytest.mark.asyncio
async def test_mark_retry(
    delivery_factory,
    notification,
    contact,
    contact_method,
    delivery_repo,
):
    delivery = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=1)

    await delivery_repo.mark_retry(delivery.id, next_attempt_at, "network error")

    updated = (await delivery_repo.get_by_notification(notification.id))[0]

    assert updated.status == DeliveryStatus.PENDING
    assert updated.attempts == 1
    assert updated.next_attempt_at is not None
    assert updated.error_message == "network error"


@pytest.mark.asyncio
async def test_mark_retry_increments_attempts(
    delivery_factory,
    notification,
    contact,
    contact_method,
    delivery_repo,
):
    delivery = await delivery_factory(
        notification_id=notification.id,
        contact_id=contact.id,
        contact_method_id=contact_method.id,
    )

    later = datetime.now(timezone.utc) + timedelta(minutes=1)

    await delivery_repo.mark_retry(delivery.id, later, "fail 1")
    await delivery_repo.mark_retry(delivery.id, later, "fail 2")

    updated = (await delivery_repo.get_by_notification(notification.id))[0]

    assert updated.attempts == 2
