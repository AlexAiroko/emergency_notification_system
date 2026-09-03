from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.providers.base import ProviderError
from app.providers import TelegramProvider


@pytest.mark.asyncio
async def test_telegram_send_success():
    with patch("app.providers.telegram.httpx.AsyncClient") as client_cls:
        client = AsyncMock()

        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "ok": True,
            "result": {"message_id": 123},
        }
        client.post.return_value = response

        client_cls.return_value = client

        provider = TelegramProvider(token="fake-token")

        message_id = await provider.send(
            to="123456",
            subject="Hello",
            body="World",
        )

        assert message_id == "123"

        client.post.assert_awaited_once()

        _, kwargs = client.post.call_args

        assert kwargs["url"].endswith("/sendMessage")

        payload = kwargs["json"]
        assert payload["chat_id"] == "123456"
        assert "<b>Hello</b>" in payload["text"]
        assert "World" in payload["text"]


@pytest.mark.asyncio
async def test_telegram_api_error():
    with patch("app.providers.telegram.httpx.AsyncClient") as client_cls:
        client = AsyncMock()

        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "ok": False,
            "description": "Bad Request",
        }
        client.post.return_value = response

        client_cls.return_value = client

        provider = TelegramProvider(token="fake-token")

        with pytest.raises(ProviderError, match="Telegram API error"):
            await provider.send(
                to="123",
                body="Hello",
            )


@pytest.mark.asyncio
async def test_telegram_http_error():
    with patch("app.providers.telegram.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client.post.side_effect = httpx.ConnectError("Connection failed")

        client_cls.return_value = client

        provider = TelegramProvider(token="fake-token")

        with pytest.raises(ProviderError, match="Telegram send failed"):
            await provider.send(
                to="123",
                body="Hello",
            )


@pytest.mark.asyncio
async def test_telegram_without_subject():
    with patch("app.providers.telegram.httpx.AsyncClient") as client_cls:
        client = AsyncMock()

        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "ok": True,
            "result": {"message_id": 10},
        }
        client.post.return_value = response

        client_cls.return_value = client

        provider = TelegramProvider(token="fake-token")

        message_id = await provider.send(
            to="123",
            body="Only body",
        )

        assert message_id == "10"

        payload = client.post.call_args.kwargs["json"]
        assert payload["text"] == "Only body"


@pytest.mark.asyncio
async def test_telegram_close_closes_client():
    with patch("app.providers.telegram.httpx.AsyncClient") as client_cls:
        client = AsyncMock()
        client_cls.return_value = client

        provider = TelegramProvider(token="fake-token")

        await provider.close()

        client.aclose.assert_awaited_once()
