import pytest

from app.models.contact_method import ChannelType


@pytest.mark.asyncio
async def test_create_contact_method(contact, contact_method_repo):
    method = await contact_method_repo.create(
        contact_id=contact.id,
        channel=ChannelType.EMAIL,
        address="john@example.com",
    )

    assert method.id is not None
    assert method.contact_id == contact.id
    assert method.channel == ChannelType.EMAIL
    assert method.address == "john@example.com"


@pytest.mark.asyncio
async def test_get_contact_method(contact_method, contact_method_repo):

    found = await contact_method_repo.get(contact_method.id)

    assert found is not None
    assert found.id == contact_method.id
    assert found.contact_id == contact_method.contact_id
    assert found.channel == contact_method.channel
    assert found.address == contact_method.address


@pytest.mark.asyncio
async def test_get_contact_method_not_found(contact_method_repo):
    result = await contact_method_repo.get(999999)
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "channels, expected_count",
    [
        ([ChannelType.EMAIL], 1),
        ([ChannelType.EMAIL, ChannelType.SMS], 2),
        ([ChannelType.EMAIL, ChannelType.SMS, ChannelType.TELEGRAM], 3),
        ([], 0),
    ],
)
async def test_get_by_contact(contact, channels, expected_count, contact_method_repo):

    for index, channel in enumerate(channels, start=1):
        await contact_method_repo.create(
            contact_id=contact.id,
            channel=channel,
            address=f"address-{index}",
        )

    methods = await contact_method_repo.get_by_contact(contact.id)

    assert len(methods) == expected_count
    assert [method.id for method in methods] == sorted(
        method.id for method in methods
    )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "target_channel, expected_addresses",
    [
        (ChannelType.EMAIL, ["a@example.com", "b@example.com"]),
        (ChannelType.SMS, ["+111"]),
        (ChannelType.TELEGRAM, []),
    ],
)
async def test_get_by_contact_and_channel(
    contact,
    target_channel,
    expected_addresses,
    contact_method_repo,
):
    await contact_method_repo.create(
        contact_id=contact.id,
        channel=ChannelType.EMAIL,
        address="a@example.com",
    )
    await contact_method_repo.create(
        contact_id=contact.id,
        channel=ChannelType.EMAIL,
        address="b@example.com",
    )
    await contact_method_repo.create(
        contact_id=contact.id,
        channel=ChannelType.SMS,
        address="+111",
    )

    methods = await contact_method_repo.get_by_contact_and_channel(
        contact.id,
        target_channel,
    )

    assert [method.address for method in methods] == expected_addresses


@pytest.mark.asyncio
async def test_get_by_contact_does_not_return_other_contacts(
    contact,
    contact_repo,
    contact_method_repo,
):
    await contact_method_repo.create(
        contact_id=contact.id,
        channel=ChannelType.EMAIL,
        address="owner@example.com",
    )

    other_contact = await contact_repo.create(name="Other")

    await contact_method_repo.create(
        contact_id=other_contact.id,
        channel=ChannelType.EMAIL,
        address="other@example.com",
    )

    methods = await contact_method_repo.get_by_contact(contact.id)

    assert len(methods) == 1
    assert methods[0].address == "owner@example.com"


@pytest.mark.asyncio
async def test_delete_contact_method(db_session, contact_method, contact_method_repo):
    await contact_method_repo.delete(contact_method.id)
    await db_session.flush()

    result = await contact_method_repo.get(contact_method.id)

    assert result is None


@pytest.mark.asyncio
async def test_delete_non_existing_contact_method(
        db_session,
        contact_method_repo,
):
    # Method shouldn't throw an exception
    await contact_method_repo.delete(999999)
    await db_session.flush()
