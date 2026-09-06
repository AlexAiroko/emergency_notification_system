import pytest

from app.exceptions.validation import EmailValidationError
from app.validators.contact_methods.email import validate_email


def test_valid_email():
    result = validate_email("user@example.com")
    assert result == "user@example.com"


def test_valid_email_normalizes():
    result = validate_email("User@Example.COM")
    assert result.lower() == "user@example.com"


def test_invalid_email():
    with pytest.raises(EmailValidationError):
        validate_email("not-an-email")


def test_empty_email():
    with pytest.raises(EmailValidationError):
        validate_email("")
