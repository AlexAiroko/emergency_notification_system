from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions.contact_import import EmptyImportFileError, InvalidImportHeaderError
from app.services.contact_import.parsers.csv_parser import CsvParser


def _make_csv(content: str) -> bytes:
    return content.encode("utf-8")


@pytest.mark.asyncio
async def test_parse_valid_csv():
    content = _make_csv(
        "external_id,name,email,telegram,phone\n"
        "ext-1,Alice,alice@test.com,@alice,\n"
        "ext-2,Bob,,@bob,+123456\n"
    )

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = CsvParser()
    rows = await parser.parse(file)

    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@test.com"
    assert rows[1]["name"] == "Bob"
    assert rows[1]["telegram"] == "@bob"


@pytest.mark.asyncio
async def test_parse_empty_csv_no_rows():
    content = _make_csv("external_id,name,email,telegram,phone\n")

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = CsvParser()
    rows = await parser.parse(file)

    assert rows == []


@pytest.mark.asyncio
async def test_parse_no_headers():
    content = _make_csv("")

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = CsvParser()

    with pytest.raises(EmptyImportFileError):
        await parser.parse(file)


@pytest.mark.asyncio
async def test_parse_invalid_headers():
    content = _make_csv("wrong,headers,here\nval1,val2,val3\n")

    file = Mock()
    file.seek = AsyncMock()
    file.read = AsyncMock(return_value=content)

    parser = CsvParser()

    with pytest.raises(InvalidImportHeaderError):
        await parser.parse(file)
