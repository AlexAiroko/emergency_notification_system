import pytest

from app.exceptions.validation import PhoneValidationError
from app.validators.contact_methods.phone import validate_phone


def test_valid_international():
    assert validate_phone("+14155552671") == "+14155552671"


def test_valid_russian():
    assert validate_phone("+79161234567") == "+79161234567"


def test_invalid_too_short():
    with pytest.raises(PhoneValidationError):
        validate_phone("123")


def test_invalid_letters():
    with pytest.raises(PhoneValidationError):
        validate_phone("abc")


def test_invalid_empty():
    with pytest.raises(PhoneValidationError):
        validate_phone("")
