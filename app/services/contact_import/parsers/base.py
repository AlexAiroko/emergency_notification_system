from abc import ABC, abstractmethod

from fastapi import UploadFile

from app.exceptions.contact_import import InvalidImportHeaderError


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
        file: UploadFile,
    ) -> list[dict]:
        """
        Reads the file and returns contacts as dictionaries.
        """
        
        raise NotImplementedError
    
    def validate_headers(
        self,
        headers: list[str],
    ) -> None:
        if tuple(headers) != self.EXPECTED_HEADERS:
            raise InvalidImportHeaderError(
                list(self.EXPECTED_HEADERS),
            )
