import pytest

from app.exceptions.validation import TelegramValidationError
from app.validators.contact_methods.telegram import validate_telegram_id


def test_valid_id():
    assert validate_telegram_id("123456789") == "123456789"


def test_valid_id_with_spaces():
    assert validate_telegram_id("  123456789  ") == "123456789"


def test_invalid_non_digit():
    with pytest.raises(TelegramValidationError):
        validate_telegram_id("abc")


def test_invalid_empty():
    with pytest.raises(TelegramValidationError):
        validate_telegram_id("")
