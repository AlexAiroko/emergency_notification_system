import logging

from app.exceptions.contact_import import UnsupportedImportFileError
from app.services.contact_import.parsers import (
    BaseContactParser,
    CsvParser,
    ExcelParser,
)


logger = logging.getLogger(__name__)


class ParserFactory:
    _PARSERS: dict[str, type[BaseContactParser]] = {
        "csv": CsvParser,
        "xlsx": ExcelParser,
    }
    
    @classmethod
    def get(cls, filename: str | None) -> BaseContactParser:
        if filename is None:
            logger.warning("Import filename is None")
            raise UnsupportedImportFileError("<unknown>")
        
        extension = filename.rsplit(".", 1)[-1].lower()
        
        parser = cls._PARSERS.get(extension)
        
        if parser is None:
            logger.warning("Unsupported import file type: %s", filename)
            raise UnsupportedImportFileError(filename)
        
        return parser()
