from typing import Optional

from src.database.models import AuditLog
from src.database.session import session_scope


SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
VALID_SEVERITIES = {SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_ERROR}

EVENT_PIPELINE_STARTED = "pipeline_started"
EVENT_TRANSCRIPTION_COMPLETE = "transcription_complete"
EVENT_INJECTION_DETECTED = "injection_detected"
EVENT_PII_DETECTED = "pii_detected"
EVENT_ANALYSIS_COMPLETE = "analysis_complete"
EVENT_REPORT_GENERATED = "report_generated"
EVENT_PIPELINE_FAILED = "pipeline_failed"
VALID_EVENT_TYPES = {
    EVENT_PIPELINE_STARTED,
    EVENT_TRANSCRIPTION_COMPLETE,
    EVENT_INJECTION_DETECTED,
    EVENT_PII_DETECTED,
    EVENT_ANALYSIS_COMPLETE,
    EVENT_REPORT_GENERATED,
    EVENT_PIPELINE_FAILED,
}


def log_event(
    event_type: str,
    message: str,
    severity: str,
    call_id: Optional[int] = None,
) -> None:
    """Write an append-only audit event to the audit_logs table."""
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
