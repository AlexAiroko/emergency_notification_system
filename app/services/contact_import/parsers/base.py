from abc import ABC, abstractmethod
import logging
from typing import AsyncGenerator

from app.exceptions.contact_import import InvalidImportHeaderError


logger = logging.getLogger(__name__)


class BaseContactParser(ABC):
    EXPECTED_HEADERS = (
        "external_id",
        "name",
        "email",
        "telegram",
        "phone",
    )
    
    @abstractmethod
    async def parse(
        self,
        filename: str,
        data: bytes,
    ) -> AsyncGenerator[dict, None]:
        """
        Reads the file and returns contacts as dictionaries.
        """
        
        raise NotImplementedError
    
    def validate_headers(
        self,
        headers: list[str],
    ) -> None:
        if tuple(headers) != self.EXPECTED_HEADERS:
            logger.warning(
                "Invalid import headers: %s (expected %s)",
                headers, self.EXPECTED_HEADERS,
            )
            raise InvalidImportHeaderError(
                list(self.EXPECTED_HEADERS),
            )
