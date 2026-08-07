from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.providers.base import ProviderError
from app.providers.email import EmailProvider


@pytest.mark.asyncio
async def test_send_success():
    provider = EmailProvider()

    with patch("app.providers.email.aiosmtplib.SMTP") as mock_smtp:
        smtp = Mock()

        smtp.connect = AsyncMock()
        smtp.starttls = AsyncMock()
        smtp.login = AsyncMock()
        smtp.send_message = AsyncMock()
        smtp.quit = AsyncMock()
        smtp.is_connected = True

        mock_smtp.return_value = smtp

        message_id = await provider.send(
            to="user@example.com",
            subject="Test Subject",
            body="Hello, world!",
        )

        mock_smtp.assert_called_once()

        smtp.connect.assert_awaited_once()
        smtp.starttls.assert_awaited_once()
        smtp.login.assert_awaited_once()
        smtp.send_message.assert_awaited_once()
        smtp.quit.assert_awaited_once()

        message = smtp.send_message.call_args.args[0]

        assert message["To"] == "user@example.com"
        assert message["Subject"] == "Test Subject"
        assert message["Message-ID"] is not None
        assert "Hello, world!" in message.get_content()

        assert message_id == message["Message-ID"]


@pytest.mark.asyncio
async def test_send_without_subject():
    provider = EmailProvider()

    with patch("app.providers.email.aiosmtplib.SMTP") as mock_smtp:
        smtp = Mock()

        smtp.connect = AsyncMock()
        smtp.starttls = AsyncMock()
        smtp.login = AsyncMock()
        smtp.send_message = AsyncMock()
        smtp.quit = AsyncMock()
        smtp.is_connected = True

        mock_smtp.return_value = smtp

        message_id = await provider.send(
            to="user@example.com",
            body="Body only",
        )

        smtp.send_message.assert_awaited_once()

        message = smtp.send_message.call_args.args[0]

        assert message["To"] == "user@example.com"
        assert message["Subject"] == ""
        assert message_id == message["Message-ID"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "smtp_method,error_message",
    [
        ("connect", "Connection failed"),
        ("starttls", "TLS failed"),
        ("login", "Authentication failed"),
        ("send_message", "Send failed"),
    ],
)
async def test_send_raises_provider_error(
    smtp_method,
    error_message,
):
    provider = EmailProvider()

    with patch("app.providers.email.aiosmtplib.SMTP") as mock_smtp:
        smtp = Mock()

        smtp.connect = AsyncMock()
        smtp.starttls = AsyncMock()
        smtp.login = AsyncMock()
        smtp.send_message = AsyncMock()
        smtp.quit = AsyncMock()
        smtp.is_connected = True

        getattr(smtp, smtp_method).side_effect = Exception(error_message)

        mock_smtp.return_value = smtp

        with pytest.raises(ProviderError) as exc:
            await provider.send(
                to="user@example.com",
                subject="Test",
                body="Hello",
            )

        assert error_message in str(exc.value)
        assert isinstance(exc.value.__cause__, Exception)

        smtp.quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_quit_not_called_if_not_connected():
    provider = EmailProvider()

    with patch("app.providers.email.aiosmtplib.SMTP") as mock_smtp:
        smtp = Mock()

        smtp.connect = AsyncMock(side_effect=Exception("Connection failed"))
        smtp.quit = AsyncMock()
        smtp.is_connected = False

        mock_smtp.return_value = smtp

        with pytest.raises(ProviderError):
            await provider.send(
                to="user@example.com",
                subject="Test",
                body="Hello",
            )

        smtp.quit.assert_not_called()
