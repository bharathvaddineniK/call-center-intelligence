import re

import config
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


REDACTED_PHONE = "[REDACTED_PHONE]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_SSN = "[REDACTED_SSN]"
REDACTED_CREDIT_CARD = "[REDACTED_CREDIT_CARD]"

FALLBACK_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", REDACTED_SSN),
    (r"\b\d{9}\b", REDACTED_SSN),
    (r"\b\d{4}-\d{4}-\d{4}-\d{4}\b", REDACTED_CREDIT_CARD),
]


analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

operators = {
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": REDACTED_PHONE}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": REDACTED_EMAIL}),
    "US_SSN": OperatorConfig("replace", {"new_value": REDACTED_SSN}),
    "CREDIT_CARD": OperatorConfig("replace", {"new_value": REDACTED_CREDIT_CARD}),
}


def redact_pii(text: str) -> tuple[str, bool]:
    """Redact supported PII from text and report whether any PII was found."""

    if text is None:
        return text, False

    results = analyzer.analyze(
        text=text,
        language="en",
        entities=config.PII_ENTITIES,
    )

    clean_text = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    final_text, regex_found = _apply_regex_fallback(clean_text.text)
    pii_found = len(results) > 0 or regex_found

    return final_text, pii_found


def _apply_regex_fallback(text: str) -> tuple[str, bool]:
    """Redact fallback regex matches missed by Presidio."""

    found = False

    for pattern, placeholder in FALLBACK_PATTERNS:
        text, count = re.subn(pattern, placeholder, text)
        found = found or count > 0

    return text, found
