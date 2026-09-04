import csv
import io
import logging

from fastapi import UploadFile

from app.exceptions.contact_import import EmptyImportFileError
from app.services.contact_import.parsers.base import BaseContactParser


logger = logging.getLogger(__name__)


class CsvParser(BaseContactParser):
    async def parse(self, file: UploadFile) -> list[dict]:
        logger.debug("Parsing CSV file: %s", file.filename)
        await file.seek(0)

        content = await file.read()
        text = content.decode("utf-8")
        
        reader = csv.DictReader(io.StringIO(text))
        
        if reader.fieldnames is None:
            raise EmptyImportFileError()
        
        self.validate_headers(list(reader.fieldnames))
        
        return list(reader)
