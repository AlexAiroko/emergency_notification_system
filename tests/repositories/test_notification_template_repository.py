import pytest


@pytest.mark.asyncio
async def test_create_template(template_repo):
    template = await template_repo.create(
        name="Welcome",
        subject="Hello",
        body="Welcome to the system",
    )

    assert template.id is not None
    assert template.name == "Welcome"
    assert template.subject == "Hello"
    assert template.body == "Welcome to the system"
    assert template.is_active is True


@pytest.mark.asyncio
async def test_create_template_with_defaults(template_repo):
    template = await template_repo.create(name="Only name", body="Only body")

    assert template.name == "Only name"
    assert template.subject is None
    assert template.body == "Only body"
    assert template.is_active is True


@pytest.mark.asyncio
async def test_get_template(notification_template, template_repo):
    found = await template_repo.get(notification_template.id)

    assert found is not None
    assert found.id == notification_template.id
    assert found.body == notification_template.body


@pytest.mark.asyncio
async def test_get_template_not_found(template_repo):
    result = await template_repo.get(999999)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statuses, expected_count",
    [
        ([True], 1),
        ([True, False, True], 2),
        ([False, False], 0),
        ([], 0),
    ],
)
async def test_get_active(statuses, expected_count, template_repo):
    for index, is_active in enumerate(statuses, start=1):
        await template_repo.create(
            name=f"Template {index}",
            subject=f"Subject {index}",
            body=f"Body {index}",
            is_active=is_active,
        )

    templates = await template_repo.get_active()

    assert len(templates) == expected_count
    assert all(template.is_active for template in templates)


@pytest.mark.asyncio
async def test_get_active_with_limit_and_offset(template_repo):
    await template_repo.create(name="Name 1", body="Body 1", is_active=True)
    await template_repo.create(name="Name 2", body="Body 2", is_active=True)
    await template_repo.create(name="Name 3", body="Body 3", is_active=True)

    templates = await template_repo.get_active(limit=2, offset=1)

    assert len(templates) == 2
    assert [template.name for template in templates] == [
        "Name 2",
        "Name 3",
    ]
    assert [template.body for template in templates] == [
        "Body 2",
        "Body 3",
    ]


@pytest.mark.asyncio
async def test_get_many(template_repo):
    await template_repo.create(name="Name 1", body="Body 1")
    await template_repo.create(name="Name 2", body="Body 2")
    await template_repo.create(name="Name 3", body="Body 3")

    templates = await template_repo.get_many(limit=2, offset=1)

    assert len(templates) == 2
    assert [template.name for template in templates] == [
        "Name 2",
        "Name 3",
    ]
    assert [template.body for template in templates] == [
        "Body 2",
        "Body 3",
    ]


@pytest.mark.asyncio
async def test_get_many_empty(template_repo):
    templates = await template_repo.get_many()

    assert templates == []


@pytest.mark.asyncio
async def test_update(notification_template, template_repo):
    await template_repo.update(
        notification_template.id,
        subject="Updated subject",
        body="Updated body",
    )

    updated = await template_repo.get(notification_template.id)

    assert updated.subject == "Updated subject"
    assert updated.body == "Updated body"
    assert updated.name == notification_template.name
    assert updated.is_active == notification_template.is_active


@pytest.mark.asyncio
async def test_deactivate_template(notification_template, template_repo):
    await template_repo.deactivate(notification_template.id)

    updated = await template_repo.get(notification_template.id)

    assert updated.is_active is False


@pytest.mark.asyncio
async def test_activate_template(notification_template, template_repo):
    await template_repo.deactivate(notification_template.id)

    await template_repo.activate(notification_template.id)

    updated = await template_repo.get(notification_template.id)

    assert updated.is_active is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name, expected_state",
    [
        ("activate", True),
        ("deactivate", False),
    ],
)
async def test_activation_methods(
    notification_template,
    method_name,
    expected_state,
    template_repo,
):
    await getattr(template_repo, method_name)(notification_template.id)

    updated = await template_repo.get(notification_template.id)

    assert updated.is_active is expected_state


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["activate", "deactivate"])
async def test_activation_methods_non_existing_template(
    method_name,
    template_repo,
):
    # Method shouldn't throw an exception
    await getattr(template_repo, method_name)(999999)
