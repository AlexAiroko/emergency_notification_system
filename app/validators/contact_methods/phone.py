import phonenumbers

from app.exceptions.validation import PhoneValidationError


def validate_phone(phone_number: str) -> str:
    try:
        parsed = phonenumbers.parse(phone_number, None)
    except phonenumbers.NumberParseException as exc:
        raise PhoneValidationError(phone_number) from exc

    if not phonenumbers.is_valid_number(parsed):
        raise PhoneValidationError(phone_number)

    return phonenumbers.format_number(
        parsed,
        phonenumbers.PhoneNumberFormat.E164,
    )

