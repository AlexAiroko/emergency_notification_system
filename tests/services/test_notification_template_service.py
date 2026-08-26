from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions.notification_template import (
    MessageTooLongError,
    TemplateAlreadyExistsError,
    TemplateBodyEmptyError,
    TemplateInactiveError,
    TemplateNotFoundError,
)


@pytest.mark.asyncio
async def test_create_template(template_service, uow):
    template = SimpleNamespace(
        id=1,
        name="name",
        is_active=True,
    )

    uow.template_repo.create = AsyncMock(return_value=template)

    result = await template_service.create_template(
        uow,
        body="body",
        name="name",
        subject="subject",
    )

    assert result is template

    uow.template_repo.create.assert_called_once_with(
        body="body",
        name="name",
        subject="subject",
        is_active=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        "",
        " ",
        "     ",
        "\n",
    ],
)
async def test_create_template_empty_body(template_service, uow, body):
    uow.template_repo.create = AsyncMock()

    with pytest.raises(
        TemplateBodyEmptyError,
        match="Template body cannot be empty",
    ):
        await template_service.create_template(
            uow,
            body=body,
            name="name",
        )

    uow.template_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_template_already_exists(template_service, uow):
    uow.template_repo.create = AsyncMock(
        side_effect=IntegrityError(
            statement="",
            params={},
            orig=Exception(),
        )
    )

    with pytest.raises(
        TemplateAlreadyExistsError,
        match="Template already exists",
    ):
        await template_service.create_template(
            uow,
            body="body",
            name="name",
        )


@pytest.mark.asyncio
async def test_get_template(template_service, uow):
    template = SimpleNamespace(id=10)

    uow.template_repo.get = AsyncMock(return_value=template)

    result = await template_service.get_template(
        uow,
        10,
    )

    assert result is template

    uow.template_repo.get.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_get_template_not_found(template_service, uow):
    uow.template_repo.get = AsyncMock(return_value=None)

    with pytest.raises(
        TemplateNotFoundError,
        match="Template 10 not found",
    ):
        await template_service.get_template(
            uow,
            10,
        )


@pytest.mark.asyncio
async def test_get_many_templates(template_service, uow):
    templates = [SimpleNamespace(id=1)]

    uow.template_repo.get_many = AsyncMock(return_value=templates)

    result = await template_service.get_many_templates(
        uow,
        limit=20,
        offset=5,
    )

    assert result == templates

    uow.template_repo.get_many.assert_called_once_with(
        limit=20,
        offset=5,
    )


@pytest.mark.asyncio
async def test_get_active_templates(template_service, uow):
    templates = [SimpleNamespace(id=1)]

    uow.template_repo.get_active = AsyncMock(return_value=templates)

    result = await template_service.get_active_templates(
        uow,
        limit=30,
        offset=10,
    )

    assert result == templates

    uow.template_repo.get_active.assert_called_once_with(
        limit=30,
        offset=10,
    )


@pytest.mark.asyncio
async def test_update_template(template_service, uow):
    template = SimpleNamespace(id=1)
    updated = SimpleNamespace(id=1)

    uow.template_repo.get = AsyncMock(return_value=template)
    uow.template_repo.update = AsyncMock(return_value=updated)

    result = await template_service.update_template(
        uow,
        template_id=1,
        subject="subj",
        body="body",
    )

    assert result is updated

    uow.template_repo.update.assert_called_once_with(
        1,
        subject="subj",
        body="body",
    )


@pytest.mark.asyncio
async def test_update_template_empty_body(template_service, uow):
    uow.template_repo.update = AsyncMock()

    with pytest.raises(
        TemplateBodyEmptyError,
        match="Template body cannot be empty",
    ):
        await template_service.update_template(
            uow,
            template_id=1,
            subject="subj",
            body=" ",
        )

    uow.template_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_activate_template(template_service, uow):
    template = SimpleNamespace(id=5)

    uow.template_repo.get = AsyncMock(return_value=template)
    uow.template_repo.activate = AsyncMock()

    await template_service.activate_template(
        uow,
        5,
    )

    uow.template_repo.activate.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_deactivate_template(template_service, uow):
    template = SimpleNamespace(id=5)

    uow.template_repo.get = AsyncMock(return_value=template)
    uow.template_repo.deactivate = AsyncMock()

    await template_service.deactivate_template(
        uow,
        5,
    )

    uow.template_repo.deactivate.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_ensure_template_is_active(template_service, uow):
    template = SimpleNamespace(
        id=10,
        is_active=True,
    )

    uow.template_repo.get = AsyncMock(return_value=template)

    result = await template_service.ensure_template_is_active(
        uow,
        10,
    )

    assert result is template


@pytest.mark.asyncio
async def test_ensure_template_not_found(template_service, uow):
    uow.template_repo.get = AsyncMock(return_value=None)

    with pytest.raises(
        TemplateNotFoundError,
        match="Template 10 not found",
    ):
        await template_service.ensure_template_is_active(
            uow,
            10,
        )


@pytest.mark.asyncio
async def test_ensure_template_inactive(template_service, uow):
    uow.template_repo.get = AsyncMock(
        return_value=SimpleNamespace(
            id=10,
            is_active=False,
        )
    )

    with pytest.raises(
        TemplateInactiveError,
        match="Template 10 is inactive",
    ):
        await template_service.ensure_template_is_active(
            uow,
            10,
        )


@pytest.mark.asyncio
async def test_create_template_rejects_long_body(template_service, uow):
    uow.template_repo.create = AsyncMock()

    with patch("app.services.notification_template.settings.MAX_MESSAGE_SIZE_BYTES", 4096):
        with pytest.raises(MessageTooLongError):
            await template_service.create_template(
                uow,
                body="x" * 5000,
                name="name",
            )

    uow.template_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_template_accepts_body_at_limit(template_service, uow):
    template = SimpleNamespace(id=1, name="name", is_active=True)

    uow.template_repo.create = AsyncMock(return_value=template)

    with patch("app.services.notification_template.settings.MAX_MESSAGE_SIZE_BYTES", 4096):
        result = await template_service.create_template(
            uow,
            body="x" * 4096,
            name="name",
        )

    assert result is template

    uow.template_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_update_template_rejects_long_body(template_service, uow):
    uow.template_repo.get = AsyncMock(return_value=SimpleNamespace(id=1))
    uow.template_repo.update = AsyncMock()

    with patch("app.services.notification_template.settings.MAX_MESSAGE_SIZE_BYTES", 4096):
        with pytest.raises(MessageTooLongError):
            await template_service.update_template(
                uow,
                template_id=1,
                subject="subj",
                body="x" * 5000,
            )

    uow.template_repo.update.assert_not_called()
