import pytest

from app.models.delivery import Delivery, DeliveryStatus


@pytest.fixture
def delivery_factory(db_session):
    async def create(**kwargs):
        delivery = Delivery(
            notification_id=kwargs["notification_id"],
            contact_id=kwargs["contact_id"],
            contact_method_id=kwargs["contact_method_id"],
            channel=kwargs.get("channel", "email"),
            address=kwargs.get("address", "test@mail.com"),
            status=kwargs.get("status", DeliveryStatus.PENDING),
            attempts=kwargs.get("attempts", 0),
            next_attempt_at=kwargs.get("next_attempt_at"),
        )

        db_session.add(delivery)
        await db_session.flush()
        return delivery

    return create


@pytest.fixture
def delivery_context(notification, contact, contact_method):
    return {
        "notification": notification,
        "contact": contact,
        "contact_method": contact_method,
    }
