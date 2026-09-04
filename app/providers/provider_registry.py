import logging

from app.models.contact_method import ChannelType
from app.providers.base import BaseProvider, ProviderError
from app.providers.email import EmailProvider
from app.providers.telegram import TelegramProvider
from app.core.config import settings


logger = logging.getLogger(__name__)


class ProviderRegistry:
    def __init__(self):
        # A list of available providers.
        # To add a new channel (e.g., WhatsApp),
        # add an object for this channel to this dictionary.
        self._providers: dict[str, BaseProvider] = {
            "email": EmailProvider(),
            "telegram": TelegramProvider(settings.TELEGRAM_BOT_TOKEN),
        }
        logger.info("Registered providers: %s", list(self._providers.keys()))

    def get(self, channel: ChannelType) -> BaseProvider:
        """
        Returns a provider by channel name.
        """
        provider = self._providers.get(channel.value)

        if provider is None:
            logger.warning("No provider for channel %s", channel.value)
            raise ProviderError(f"No provider registered for channel {channel}")

        return provider

    async def close_all(self) -> None:
        logger.info("Closing all providers")
        for provider in self._providers.values():
            await provider.close()
        logger.info("All providers closed")
