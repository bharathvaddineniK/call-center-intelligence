import pytest

from src.security.pii_redactor import (
    REDACTED_CREDIT_CARD,
    REDACTED_EMAIL,
    REDACTED_PHONE,
    REDACTED_SSN,
    redact_pii,
)


SSN_VARIANTS = [
    "123-45-6789",
    "123456789",
    "123 45 6789",
    "123.45.6789",
    "123/45/6789",
]

PHONE_VARIANTS = [
    "555-123-4567",
    "(555) 123-4567",
    "+1-555-123-4567",
    "5551234567",
    "555.123.4567",
]

EMAIL_VARIANTS = [
    "john@gmail.com",
    "john.doe@company.co.uk",
    "john+tag@example.org",
    "support_team@example.com",
    "first_last99@subdomain.company.io",
]

CREDIT_CARD_VARIANTS = [
    "1234-5678-9012-3456",
    "1234567890123456",
    "1234 5678 9012 3456",
    "4111-1111-1111-1111",
    "4111 1111 1111 1111",
]


@pytest.mark.parametrize("ssn", SSN_VARIANTS)
def test_ssn_variants_redacted(ssn):
    """Redact supported SSN format variants."""
    text = f"The customer's social is {ssn}."
    result, pii_found = redact_pii(text)

    assert REDACTED_SSN in result
    assert ssn not in result
    assert pii_found is True


@pytest.mark.parametrize("phone", PHONE_VARIANTS)
def test_phone_variants_redacted(phone):
    """Redact supported phone number format variants."""
    text = f"The customer's phone number is {phone}."
    result, pii_found = redact_pii(text)

    assert REDACTED_PHONE in result
    assert phone not in result
    assert pii_found is True


@pytest.mark.parametrize("email", EMAIL_VARIANTS)
def test_email_variants_redacted(email):
    """Redact supported email address format variants."""
    text = f"Please contact the customer at {email}."
    result, pii_found = redact_pii(text)

    assert REDACTED_EMAIL in result
    assert email not in result
    assert pii_found is True


@pytest.mark.parametrize("credit_card", CREDIT_CARD_VARIANTS)
def test_credit_card_variants_redacted(credit_card):
    """Redact supported credit card format variants."""
    text = f"The customer's card number is {credit_card}."
    result, pii_found = redact_pii(text)

    assert REDACTED_CREDIT_CARD in result
    assert credit_card not in result
    assert pii_found is True


def test_clean_text_unchanged():
    """Leave clean text unchanged and report that no PII was found."""
    text = "Reach me out at email if I do not pick calls"
    result, pii_found = redact_pii(text)

    assert result == text
    assert pii_found is False


def test_none_input_handled():
    """Handle None input without reporting PII."""
    text = None
    result, pii_found = redact_pii(text)

    assert result is None
    assert pii_found is False
