import logging
import re

from jinja2 import Environment, BaseLoader, TemplateSyntaxError, UndefinedError

from app.exceptions.notification_template import TemplateRenderError
from app.models.contact import Contact
from app.models.notification_template import NotificationTemplate


logger = logging.getLogger(__name__)

_env = Environment(loader=BaseLoader(), autoescape=False)

SYSTEM_VARIABLES = {"name", "contact_id"}


class TemplateRenderer:
    @staticmethod
    def render_subject(
        template: NotificationTemplate,
        contact: Contact,
        variables: dict,
    ) -> str | None:
        if template.subject is None:
            return None
        return TemplateRenderer._render(template.subject, contact, variables)

    @staticmethod
    def render_body(
        template: NotificationTemplate,
        contact: Contact,
        variables: dict,
    ) -> str:
        return TemplateRenderer._render(template.body, contact, variables)

    @staticmethod
    def _render(
        text: str,
        contact: Contact,
        variables: dict,
    ) -> str:
        try:
            tpl = _env.from_string(text)
            return tpl.render(
                name=contact.name,
                contact_id=contact.id,
                **variables,
            )
        except (TemplateSyntaxError, UndefinedError) as exc:
            logger.warning("Template render failed: %s", exc)
            raise TemplateRenderError(str(exc)) from exc

    @staticmethod
    def validate_variables(body: str, variables: dict, subject: str | None = None) -> list[str]:
        combined = body
        if subject:
            combined = subject + " " + body
        used = set(re.findall(r"\{\{(\w+)\}\}", combined))
        provided = set(variables.keys()) | SYSTEM_VARIABLES
        return sorted(used - provided)
