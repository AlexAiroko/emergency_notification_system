import pytest

from app.exceptions.contact_import import UnsupportedImportFileError
from app.services.contact_import.parsers.csv_parser import CsvParser
from app.services.contact_import.parsers.excel_parser import ExcelParser
from app.services.contact_import.parser_factory import ParserFactory


def test_get_csv():
    parser = ParserFactory.get("contacts.csv")
    assert isinstance(parser, CsvParser)


def test_get_xlsx():
    parser = ParserFactory.get("contacts.xlsx")
    assert isinstance(parser, ExcelParser)


def test_get_none():
    with pytest.raises(UnsupportedImportFileError):
        ParserFactory.get(None)


def test_get_unsupported():
    with pytest.raises(UnsupportedImportFileError):
        ParserFactory.get("contacts.json")
