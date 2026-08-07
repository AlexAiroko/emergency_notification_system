import pytest_asyncio

from app.models.contact import Contact
from app.models.contact_method import ChannelType, ContactMethod


@pytest_asyncio.fixture
async def contact(db_session):
    obj = Contact(name="Alice")
    db_session.add(obj)
    await db_session.flush()
    return obj


@pytest_asyncio.fixture
async def extra_contacts(db_session):
    c2 = Contact(name="Bob")
    c3 = Contact(name="Bobby")
    db_session.add_all([c2, c3])
    await db_session.flush()

    cm2 = ContactMethod(
        contact_id=c2.id,
        channel=ChannelType.SMS,
        address="+123456789",
    )
    cm3 = ContactMethod(
        contact_id=c3.id,
        channel=ChannelType.EMAIL,
        address="abc@abc.com",
    )
    db_session.add_all([cm2, cm3])
    await db_session.flush()

    return (c2, cm2), (c3, cm3)


@pytest_asyncio.fixture
async def second_contact_with_method(db_session):
    contact = Contact(name="B")
    db_session.add(contact)
    await db_session.flush()

    method = ContactMethod(
        contact_id=contact.id,
        channel=ChannelType.SMS,
        address="+111",
    )
    db_session.add(method)
    await db_session.flush()

    return contact, method
