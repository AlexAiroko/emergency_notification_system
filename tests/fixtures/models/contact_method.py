import pytest

from app.models.contact_method import ChannelType, ContactMethod


@pytest.fixture
async def contact_method(db_session, contact):
    obj = ContactMethod(
        contact_id=contact.id,
        channel=ChannelType.EMAIL,
        address="a@a.com",
    )
    db_session.add(obj)
    await db_session.flush()
    return obj
