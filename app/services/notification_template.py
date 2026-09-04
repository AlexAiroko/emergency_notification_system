import logging

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.uow import UnitOfWork
from app.exceptions.notification_template import (
    MessageTooLongError,
    TemplateAlreadyExistsError, 
    TemplateBodyEmptyError, 
    TemplateInactiveError, 
    TemplateNotFoundError,
)
from app.models import NotificationTemplate



logger = logging.getLogger(__name__)


class NotificationTemplateService:
    async def _get_template(
        self,
        uow: UnitOfWork,
        template_id: int,
    ) -> NotificationTemplate:
        template = await uow.template_repo.get(template_id)

        if template is None:
            logger.warning("Template %s not found", template_id)
            raise TemplateNotFoundError(template_id)

        return template

    async def create_template(
        self,
        uow: UnitOfWork,
        body: str,
        name: str,
        subject: str | None = None,
        is_active: bool = True,
    ) -> NotificationTemplate:
        """
        Creates a new template.

        Business rules:
        - body must not be empty.
        """
        
        self._validate_body(body)

        try:
            template = await uow.template_repo.create(
                body=body,
                name=name,
                subject=subject,
                is_active=is_active,
            )

            logger.info(
                "Template %s created (name=%s, active=%s)",
                template.id,
                template.name,
                template.is_active,
            )

            return template
        except IntegrityError as exc:
            logger.warning(
                "Failed to create template: template with name '%s' already exists",
                name,
            )
            
            raise TemplateAlreadyExistsError() from exc

    async def get_template(self, uow: UnitOfWork, template_id: int) -> NotificationTemplate | None:
        """
        Returns a template by ID.
        """
        
        return await self._get_template(uow, template_id)

    async def get_many_templates(
        self,
        uow: UnitOfWork,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NotificationTemplate]:
        """
        Returns a list of all templates.
        """
        
        return await uow.template_repo.get_many(
            limit=limit,
            offset=offset,
        )

    async def get_active_templates(
        self,
        uow: UnitOfWork,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NotificationTemplate]:
        """
        Returns only active templates.
        """
        
        return await uow.template_repo.get_active(
            limit=limit,
            offset=offset,
        )

    async def update_template(
        self,
        uow: UnitOfWork,
        template_id: int,
        subject: str | None,
        body: str,
    ) -> NotificationTemplate:
        """
        Updates the template's subject and body.

        Business rules:
        - body must not be empty.
        """
        
        self._validate_body(body)

        await self._get_template(uow, template_id)

        # The repository expects a string, so we replace None with an empty string.
        updated = await uow.template_repo.update(
            template_id,
            subject=subject,
            body=body,
        )
        
        logger.info(
            "Template %s updated",
            template_id,
        )

        return updated

    async def activate_template(self, uow: UnitOfWork, template_id: int) -> None:
        """
        Makes the template active.
        """

        await self._get_template(uow, template_id)
        await uow.template_repo.activate(template_id)
        
        logger.info(
            "Template %s activated",
            template_id,
        )

    async def deactivate_template(self, uow: UnitOfWork, template_id: int) -> None:
        """
        Makes the template inactive.
        """

        await self._get_template(uow, template_id)
        await uow.template_repo.deactivate(template_id)
        
        logger.info(
            "Template %s deactivated",
            template_id,
        )

    async def ensure_template_is_active(
        self,
        uow: UnitOfWork,
        template_id: int,
    ) -> NotificationTemplate:
        """
        Returns the template if it exists and is active.
        """
        
        template = await self._get_template(uow, template_id)

        if not template.is_active:
            logger.warning("Template %s is inactive", template_id)
            raise TemplateInactiveError(template_id)

        return template

    def _validate_body(self, body: str) -> None:
        """
        Checks that the body is non-empty.
        """
        
        if not body or not body.strip():
            logger.warning("Template body is empty")
            raise TemplateBodyEmptyError()

        size = len(body.encode("utf-8"))
        if size > settings.MAX_MESSAGE_SIZE_BYTES:
            logger.warning(
                "Template body too long: %s bytes (max %s)",
                size, settings.MAX_MESSAGE_SIZE_BYTES,
            )
            raise MessageTooLongError(size, settings.MAX_MESSAGE_SIZE_BYTES)
