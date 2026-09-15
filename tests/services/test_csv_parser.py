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

    parser = CsvParser()
    rows = []
    async for row in parser.parse("contacts.csv", content):
        rows.append(row)

    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@test.com"
    assert rows[1]["name"] == "Bob"
    assert rows[1]["telegram"] == "@bob"


@pytest.mark.asyncio
async def test_parse_empty_csv_no_rows():
    content = _make_csv("external_id,name,email,telegram,phone\n")

    parser = CsvParser()
    rows = []
    async for row in parser.parse("contacts.csv", content):
        rows.append(row)

    assert rows == []


@pytest.mark.asyncio
async def test_parse_no_headers():
    content = _make_csv("")

    parser = CsvParser()

    with pytest.raises(EmptyImportFileError):
        async for _ in parser.parse("contacts.csv", content):
            pass


@pytest.mark.asyncio
async def test_parse_invalid_headers():
    content = _make_csv("wrong,headers,here\nval1,val2,val3\n")

    parser = CsvParser()

    with pytest.raises(InvalidImportHeaderError):
        async for _ in parser.parse("contacts.csv", content):
            pass


@pytest.mark.asyncio
async def test_parse_csv_with_bom():
    content = (
        b"\xef\xbb\xbf"
        b"external_id,name,email,telegram,phone\n"
        b"ext-1,Alice,alice@test.com,@alice,\n"
    )

    parser = CsvParser()
    rows = []
    async for row in parser.parse("contacts.csv", content):
        rows.append(row)

    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
