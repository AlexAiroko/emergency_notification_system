import logging

from email.message import EmailMessage
from email.utils import make_msgid

import aiosmtplib

from app.core.config import settings
from app.providers.base import BaseProvider, ProviderError


logger = logging.getLogger(__name__)


class EmailProvider(BaseProvider):
    def __init__(self) -> None:
        self._smtp: aiosmtplib.SMTP | None = None

    async def _ensure_connection(self) -> aiosmtplib.SMTP:
        if self._smtp is None:
            self._smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                timeout=30,
            )

        if not self._smtp.is_connected:
            await self._smtp.connect()
            if settings.SMTP_USE_TLS:
                logger.info("Starting TLS for email delivery")
                await self._smtp.starttls()
            logger.info("Authenticating SMTP user=%s", settings.SMTP_USERNAME)
            await self._smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        return self._smtp

    async def send(
        self,
        to: str,
        body: str,
        subject: str | None = None,
    ) -> str | None:
        logger.info(
            "Started sending email (host=%s, port=%s, to=%s)",
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            to,
        )

        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject or ""
        message["Message-ID"] = make_msgid()
        message.set_content(body)

        try:
            smtp = await self._ensure_connection()

            await smtp.send_message(message)

            logger.info(
                "Email sent successfully (to=%s, message_id=%s)",
                to,
                message["Message-ID"],
            )
            
            # SMTP usually does not return a message_id, 
            # so we use the Message-ID header.

            return message["Message-ID"]

        except Exception as exc:
            self._smtp = None
            logger.exception(
                "Failed to send email (to=%s)",
                to,
            )
            raise ProviderError(str(exc)) from exc

    async def close(self) -> None:
        if self._smtp is not None and self._smtp.is_connected:
            await self._smtp.quit()
        self._smtp = None
