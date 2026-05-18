from src.database.models import AuditLog
from src.database.session import session_scope

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
VALID_SEVERITIES = {SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_ERROR}

EVENT_INTAKE = "intake"
EVENT_TRANSCRIPTION = "transcription"
EVENT_INJECTION_SCAN = "injection_scan"
EVENT_PII_SCAN = "pii_scan"
EVENT_SUMMARY = "summary"
EVENT_QA_SCORING = "qa_scoring"
EVENT_SUPERVISOR_REVIEW = "supervisor_review"
EVENT_REPORT_GENERATION = "report_generation"
EVENT_PIPELINE = "pipeline"

# Outcome-specific names are kept as aliases so existing imports continue to work,
# but new rows use stable stage-level event names.
EVENT_INTAKE_VALIDATED = EVENT_INTAKE
EVENT_TRANSCRIPTION_COMPLETED = EVENT_TRANSCRIPTION
EVENT_TRANSCRIPTION_CACHE_HIT = EVENT_TRANSCRIPTION
EVENT_INJECTION_SCAN_CLEAN = EVENT_INJECTION_SCAN
EVENT_INJECTION_DETECTED = EVENT_INJECTION_SCAN
EVENT_PII_SCAN_CLEAN = EVENT_PII_SCAN
EVENT_PII_REDACTED = EVENT_PII_SCAN
EVENT_SUMMARY_GENERATED = EVENT_SUMMARY
EVENT_QA_SCORING_COMPLETED = EVENT_QA_SCORING
EVENT_SUPERVISOR_REVIEW_FLAGGED = EVENT_SUPERVISOR_REVIEW
EVENT_REPORT_GENERATED = EVENT_REPORT_GENERATION
EVENT_PIPELINE_FAILED = EVENT_PIPELINE

# Backward-compatible aliases for older imports/tests.
EVENT_PIPELINE_STARTED = EVENT_INTAKE_VALIDATED
EVENT_TRANSCRIPTION_COMPLETE = EVENT_TRANSCRIPTION_COMPLETED
EVENT_PII_DETECTED = EVENT_PII_REDACTED
EVENT_ANALYSIS_COMPLETE = EVENT_SUMMARY_GENERATED

VALID_EVENT_TYPES = {
    EVENT_INTAKE,
    EVENT_TRANSCRIPTION,
    EVENT_INJECTION_SCAN,
    EVENT_PII_SCAN,
    EVENT_SUMMARY,
    EVENT_QA_SCORING,
    EVENT_SUPERVISOR_REVIEW,
    EVENT_REPORT_GENERATION,
    EVENT_PIPELINE,
}


def log_event(
    event_type: str,
    message: str,
    severity: str,
    call_id: int | None = None,
) -> None:
    """Write an append-only audit event to the audit_log table."""
    _validate_event_type(event_type)
    _validate_severity(severity)

    with session_scope() as session:
        session.add(
            AuditLog(
                call_id=call_id,
                event_type=event_type,
                message=message,
                severity=severity,
            )
        )


def _validate_event_type(event_type: str) -> None:
    """Raise a clear error for unsupported audit event types."""
    if event_type not in VALID_EVENT_TYPES:
        valid_events = ", ".join(sorted(VALID_EVENT_TYPES))
        raise ValueError(f"Invalid audit event type '{event_type}'. Use one of: {valid_events}.")


def _validate_severity(severity: str) -> None:
    """Raise a clear error for unsupported audit severity values."""
    if severity not in VALID_SEVERITIES:
        valid_severities = ", ".join(sorted(VALID_SEVERITIES))
        raise ValueError(f"Invalid audit severity '{severity}'. Use one of: {valid_severities}.")
