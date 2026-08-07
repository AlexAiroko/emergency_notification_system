import csv
import io

from fastapi import UploadFile

from app.exceptions.contact_import import EmptyImportFileError
from app.services.contact_import.parsers.base import BaseContactParser


class CsvParser(BaseContactParser):
    async def parse(self, file: UploadFile) -> list[dict]:
        await file.seek(0)

        content = await file.read()
        text = content.decode("utf-8")
        
        reader = csv.DictReader(io.StringIO(text))
        
        if reader.fieldnames is None:
            raise EmptyImportFileError()
        
        self.validate_headers(list(reader.fieldnames))
        
        return list(reader)
