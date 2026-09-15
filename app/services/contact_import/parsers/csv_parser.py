import csv
import io
import logging
from typing import AsyncGenerator

from app.exceptions.contact_import import EmptyImportFileError
from app.services.contact_import.parsers.base import BaseContactParser


logger = logging.getLogger(__name__)


class CsvParser(BaseContactParser):
    async def parse(self, filename: str, data: bytes) -> AsyncGenerator[dict, None]:
        logger.debug("Parsing CSV file: %s", filename)

        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        if reader.fieldnames is None:
            raise EmptyImportFileError()

        self.validate_headers(list(reader.fieldnames))

        for row in reader:
            yield row
