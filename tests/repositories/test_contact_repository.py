import pytest
from sqlalchemy import inspect

from app.models.contact_method import ChannelType, ContactMethod


@pytest.mark.asyncio
async def test_create_contact(contact_repo):
    contact = await contact_repo.create(
        name="John Doe",
        external_id="ext-123",
    )
    
    assert contact.id is not None
    assert contact.name == "John Doe"
    assert contact.external_id == "ext-123"


@pytest.mark.asyncio
async def test_create_contact_with_null_external_id(contact_repo):
    contact = await contact_repo.create(name="NoExternal")
    contact_id = contact.id

    db_contact = await contact_repo.get(contact_id)

    assert db_contact.external_id is None
    assert db_contact.name == "NoExternal"
    

@pytest.mark.asyncio
async def test_create_persists_to_db(db_session, contact_repo):
    contact = await contact_repo.create(name="Persist")
    contact_id = contact.id

    loaded = await contact_repo.get(contact_id)

    assert loaded is not None
    assert loaded.name == "Persist"


@pytest.mark.asyncio
async def test_get_contact(contact_repo):
    created = await contact_repo.create(name="Alice")

    found = await contact_repo.get(created.id)
    
    assert found.id is not None
    assert found.id == created.id
    assert found.name == "Alice"


@pytest.mark.asyncio
async def test_get_contact_not_found(contact_repo):
    result = await contact_repo.get(999999)

    assert result is None


@pytest.mark.asyncio
async def test_get_many_order(contact_repo):
    await contact_repo.create(name="A")
    await contact_repo.create(name="B")
    await contact_repo.create(name="C")

    result = await contact_repo.get_many(limit=3)

    assert [c.name for c in result] == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_get_many_empty(contact_repo):
    result = await contact_repo.get_many()

    assert result == []


@pytest.mark.asyncio
async def test_get_many_contacts_limit_no_offset(contact_repo):
    await contact_repo.create(name="User 1")
    await contact_repo.create(name="User 2")
    await contact_repo.create(name="User 3")
    
    contacts = await contact_repo.get_many(limit=2, offset=0)
    
    assert len(contacts) == 2
    assert contacts[0].name == "User 1"
    assert contacts[1].name == "User 2"


@pytest.mark.asyncio
async def test_get_many_contacts_limit_offset(contact_repo):
    await contact_repo.create(name="User 1")
    await contact_repo.create(name="User 2")
    await contact_repo.create(name="User 3")
    
    contacts = await contact_repo.get_many(limit=2, offset=1)
    
    assert len(contacts) == 2
    assert contacts[0].name == "User 2"
    assert contacts[1].name == "User 3"


@pytest.mark.asyncio
async def test_get_many_limit_zero(contact_repo):
    await contact_repo.create(name="A")
    await contact_repo.create(name="B")

    result = await contact_repo.get_many(limit=0)

    assert result == []


@pytest.mark.asyncio
async def test_get_many_offset_beyond_size(contact_repo):
    await contact_repo.create(name="A")
    await contact_repo.create(name="B")

    result = await contact_repo.get_many(limit=10, offset=100)

    assert result == []


@pytest.mark.asyncio
async def test_get_with_methods(db_session, contact_repo):
    contact = await contact_repo.create(name="Bob")
    contact_id = contact.id
    
    db_session.add_all(
        [
            ContactMethod(
                contact_id=contact_id,
                channel=ChannelType.EMAIL,
                address="bob@example.com",
            ),
            ContactMethod(
                contact_id=contact_id,
                channel=ChannelType.SMS,
                address="+123456789",
            ),
        ]
    )
    
    await db_session.flush()
    
    result = await contact_repo.get_with_methods(contact_id)
    
    assert result is not None
    assert result.id == contact_id
    assert len(result.contact_methods) == 2
    assert result.contact_methods[0].address in {
        "bob@example.com",
        "+123456789",
    }


@pytest.mark.asyncio
async def test_get_with_methods_not_found(contact_repo):
    result = await contact_repo.get_with_methods(999999)

    assert result is None


@pytest.mark.asyncio
async def test_get_with_methods_empty(contact_repo):
    contact = await contact_repo.create(name="Solo")
    contact_id = contact.id

    result = await contact_repo.get_with_methods(contact_id)

    assert result is not None
    assert result.contact_methods == []


@pytest.mark.asyncio
async def test_get_with_methods_eager_loaded(db_session, contact_repo):
    contact = await contact_repo.create(name="Bob")
    contact_id = contact.id

    db_session.add_all([
        ContactMethod(
            contact_id=contact_id,
            channel=ChannelType.EMAIL,
            address="a@a.com",
        )
    ])
    await db_session.flush()

    result = await contact_repo.get_with_methods(contact_id)

    # check that the relation is already loaded
    state = inspect(result)
    assert "contact_methods" not in state.unloaded


@pytest.mark.asyncio
async def test_contact_methods_belong_to_contact(db_session, contact_repo):
    contact = await contact_repo.create(name="Owner")
    contact_id = contact.id

    db_session.add_all([
        ContactMethod(
            contact_id=contact_id,
            channel=ChannelType.EMAIL,
            address="owner@mail.com",
        ),
        ContactMethod(
            contact_id=contact_id,
            channel=ChannelType.SMS,
            address="+111",
        ),
    ])

    await db_session.flush()

    result = await contact_repo.get_with_methods(contact_id)

    assert all(cm.contact_id == contact_id for cm in result.contact_methods)


@pytest.mark.asyncio
async def test_create_inactive_contact(db_session, contact_repo):
    contact = await contact_repo.create(
        name="Inactive",
        is_active=False,
    )

    assert contact.is_active is False

    loaded = await contact_repo.get(contact.id)

    assert loaded.is_active is False


@pytest.mark.asyncio
async def test_get_active_contacts(contact_repo):
    await contact_repo.create(name="A")
    await contact_repo.create(name="B", is_active=False)
    await contact_repo.create(name="C")

    contacts = await contact_repo.get_active()

    assert len(contacts) == 2
    assert [c.name for c in contacts] == ["A", "C"]


@pytest.mark.asyncio
async def test_get_active_contacts_limit_offset(contact_repo):
    await contact_repo.create(name="A")
    await contact_repo.create(name="B", is_active=False)
    await contact_repo.create(name="C")
    await contact_repo.create(name="D")

    contacts = await contact_repo.get_active(
        limit=1,
        offset=1,
    )

    assert len(contacts) == 1
    assert contacts[0].name == "C"


@pytest.mark.asyncio
async def test_get_active_contacts_empty(contact_repo):
    await contact_repo.create(name="A", is_active=False)
    await contact_repo.create(name="B", is_active=False)

    contacts = await contact_repo.get_active()

    assert contacts == []


@pytest.mark.asyncio
async def test_update_contact(db_session, contact_repo):
    contact = await contact_repo.create(name="Old")
    contact_id = contact.id

    await contact_repo.update(
        contact_id,
        name="New",
    )

    updated = await contact_repo.get(contact_id)

    assert updated.name == "New"


@pytest.mark.asyncio
async def test_update_not_existing_contact(contact_repo):
    await contact_repo.update(
        999999,
        name="New",
    )

    contact = await contact_repo.get(999999)

    assert contact is None


@pytest.mark.asyncio
async def test_activate_contact(db_session, contact_repo):
    contact = await contact_repo.create(
        name="User",
        is_active=False,
    )
    contact_id = contact.id

    await contact_repo.activate(contact_id)

    contact = await contact_repo.get(contact_id)

    assert contact.is_active is True


@pytest.mark.asyncio
async def test_deactivate_contact(db_session, contact_repo):
    contact = await contact_repo.create(name="User")
    contact_id = contact.id

    await contact_repo.deactivate(contact_id)

    contact = await contact_repo.get(contact_id)

    assert contact.is_active is False


@pytest.mark.asyncio
async def test_activate_then_deactivate_contact(db_session, contact_repo):
    contact = await contact_repo.create(
        name="User",
        is_active=False,
    )
    contact_id = contact.id

    await contact_repo.activate(contact_id)
    contact = await contact_repo.get(contact_id)

    assert contact.is_active is True

    await contact_repo.deactivate(contact_id)
    contact = await contact_repo.get(contact_id)

    assert contact.is_active is False


@pytest.mark.asyncio
async def test_update_does_not_change_external_id(db_session, contact_repo):
    contact = await contact_repo.create(
        name="Old",
        external_id="ext-123",
    )
    contact_id = contact.id

    await contact_repo.update(contact_id, name="New")

    updated = await contact_repo.get(contact_id)

    assert updated.name == "New"
    assert updated.external_id == "ext-123"
