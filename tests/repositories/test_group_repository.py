import pytest

from app.models.contact import Contact
from app.models.contact_method import ContactMethod, ChannelType

@pytest.mark.asyncio
async def test_create_group(group_repo):
    group = await group_repo.create(name="Admins")

    assert group.id is not None
    assert group.name == "Admins"


@pytest.mark.asyncio
async def test_get_group(group_repo):
    created = await group_repo.create(name="Team")

    found = await group_repo.get(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Team"


@pytest.mark.asyncio
async def test_get_group_not_found(group_repo):
    result = await group_repo.get(999999)

    assert result is None


@pytest.mark.asyncio
async def test_get_with_contacts_empty(group_repo):
    group = await group_repo.create(name="Empty Group")

    result = await group_repo.get_with_contacts(group.id)

    assert result is not None
    assert result.contacts == []


@pytest.mark.asyncio
async def test_add_contact_to_group(db_session, group_repo):
    group = await group_repo.create(name="G1")

    contact = Contact(name="Alice")
    db_session.add(contact)
    await db_session.flush()

    await group_repo.add_contact(group.id, contact.id)

    result = await group_repo.get_with_contacts(group.id)

    assert len(result.contacts) == 1
    assert result.contacts[0].id == contact.id


@pytest.mark.asyncio
async def test_group_multiple_contacts(db_session, group_repo):
    group = await group_repo.create(name="G1")

    c1 = Contact(name="A")
    c2 = Contact(name="B")

    db_session.add_all([c1, c2])
    await db_session.flush()

    await group_repo.add_contact(group.id, c1.id)
    await group_repo.add_contact(group.id, c2.id)

    result = await group_repo.get_with_contacts(group.id)

    ids = {c.id for c in result.contacts}

    assert ids == {c1.id, c2.id}


@pytest.mark.asyncio
async def test_remove_contact_from_group(db_session, group_repo):
    group = await group_repo.create(name="G1")

    contact = Contact(name="Alice")
    db_session.add(contact)
    await db_session.flush()

    await group_repo.add_contact(group.id, contact.id)

    await group_repo.remove_contact_from_group(group.id, contact.id)
    await db_session.flush()

    result = await group_repo.get_with_contacts(group.id)

    assert result.contacts == []


@pytest.mark.asyncio
async def test_remove_non_existing_contact_does_not_fail(db_session, group_repo):
    group = await group_repo.create(name="G1")

    await group_repo.remove_contact_from_group(group.id, 999999)
    await db_session.flush()

    result = await group_repo.get(group.id)

    assert result is not None


@pytest.mark.asyncio
async def test_get_contacts_for_dispatch_empty(group_repo):
    group = await group_repo.create(name="G1")

    result = await group_repo.get_contacts_for_dispatch(group.id)

    assert result == []


@pytest.mark.asyncio
async def test_get_contacts_for_dispatch(db_session, group_repo):
    group = await group_repo.create(name="G1")

    contact = Contact(name="Bob")
    db_session.add(contact)
    await db_session.flush()

    db_session.add(
        ContactMethod(
            contact_id=contact.id,
            channel=ChannelType.EMAIL,
            address="bob@mail.com",
        )
    )

    await group_repo.add_contact(group.id, contact.id)

    result = await group_repo.get_contacts_for_dispatch(group.id)

    assert len(result) == 1
    assert result[0].id == contact.id
    assert len(result[0].contact_methods) == 1
