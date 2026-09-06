import pytest

from app.models.contact_method import ChannelType
from app.validators.contact_methods.registry import ContactMethodValidatorRegistry


def test_validate_email():
    result = ContactMethodValidatorRegistry.validate(ChannelType.EMAIL, "ok@test.com")
    assert result == "ok@test.com"


def test_validate_telegram():
    result = ContactMethodValidatorRegistry.validate(ChannelType.TELEGRAM, "123456")
    assert result == "123456"


def test_validate_phone():
    result = ContactMethodValidatorRegistry.validate(ChannelType.SMS, "+14155552671")
    assert result == "+14155552671"


def test_invalid_email_raises():
    from app.exceptions.validation import EmailValidationError

    with pytest.raises(EmailValidationError):
        ContactMethodValidatorRegistry.validate(ChannelType.EMAIL, "bad")
