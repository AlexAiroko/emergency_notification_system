import asyncio
from io import BytesIO
import logging
from typing import AsyncGenerator

from openpyxl import load_workbook

from app.exceptions.contact_import import EmptyImportFileError
from app.services.contact_import.parsers.base import BaseContactParser


logger = logging.getLogger(__name__)


class ExcelParser(BaseContactParser):
    async def parse(self, filename: str, data: bytes) -> AsyncGenerator[dict, None]:
        logger.debug("Parsing Excel file: %s", filename)

        workbook = await asyncio.to_thread(
            load_workbook, BytesIO(data)
        )

        sheet = workbook.active
        if sheet is None:
            raise EmptyImportFileError()
        rows = list(sheet.iter_rows(values_only=True))

        if not rows:
            raise EmptyImportFileError()

        headers = list(rows[0])
        self.validate_headers(headers)

        for values in rows[1:]:
            yield dict(zip(headers, values))
