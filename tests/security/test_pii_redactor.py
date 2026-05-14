from src.security.pii_redactor import redact_pii


def test_ssn_redacted():
    """Redact SSNs and report that PII was found."""

    text = "I'm not sure if I could share my social but it's 123-45-6789"
    result, pii_found = redact_pii(text)

    assert result == "I'm not sure if I could share my social but it's [REDACTED_SSN]"
    assert pii_found is True


def test_email_redacted():
    """Redact email addresses and report that PII was found."""

    text = "Why do not you reach me out at myeamil@example.com"
    result, pii_found = redact_pii(text)

    assert result == "Why do not you reach me out at [REDACTED_EMAIL]"
    assert pii_found is True


def test_phone_redacted():
    """Redact phone numbers and report that PII was found."""

    text = "I'm always available at 555-123-4567"
    result, pii_found = redact_pii(text)

    assert result == "I'm always available at [REDACTED_PHONE]"
    assert pii_found is True


def test_clean_text_unchanged():
    """Leave clean text unchanged and report that no PII was found."""

    text = "Reach me out at email if I do not pick calls"
    result, pii_found = redact_pii(text)

    assert result == "Reach me out at email if I do not pick calls"
    assert pii_found is False


def test_none_input_handled():
    """Handle None input without reporting PII."""

    text = None
    result, pii_found = redact_pii(text)

    assert result is None
    assert pii_found is False
