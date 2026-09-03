from io import BytesIO
from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions.contact_import import EmptyImportFileError, InvalidImportHeaderError
from app.services.contact_import.parsers.excel_parser import ExcelParser


def _make_xlsx(rows: list[list]) -> bytes:
    """Helper: creates a minimal XLSX file in memory."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active

    for row in rows:
        ws.append(row)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


@pytest.mark.asyncio
async def test_parse_valid_xlsx():
    content = _make_xlsx([
        ["external_id", "name", "email", "telegram", "phone"],
        ["ext-1", "Alice", "alice@test.com", "@alice", ""],
        ["ext-2", "Bob", "", "@bob", "+123456"],
    ])

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = ExcelParser()
    rows = await parser.parse(file)

    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@test.com"
    assert rows[1]["name"] == "Bob"
    assert rows[1]["telegram"] == "@bob"


@pytest.mark.asyncio
async def test_parse_empty_xlsx():
    content = _make_xlsx([])

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = ExcelParser()

    with pytest.raises(EmptyImportFileError):
        await parser.parse(file)


@pytest.mark.asyncio
async def test_parse_invalid_headers():
    content = _make_xlsx([
        ["wrong", "headers", "here"],
        ["val1", "val2", "val3"],
    ])

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = ExcelParser()

    with pytest.raises(InvalidImportHeaderError):
        await parser.parse(file)
