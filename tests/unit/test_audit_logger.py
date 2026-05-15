import pytest

from src.database.models import AuditLog
from src.database.session import init_db, session_scope
from src.security.audit_logger import (
    EVENT_PIPELINE_FAILED,
    EVENT_PIPELINE_STARTED,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    log_event,
)


def test_log_event_writes_audit_log():
    """Test that log_event creates an audit log record."""
    init_db()

    log_event(
        event_type=EVENT_PIPELINE_STARTED,
        message="Pipeline started",
        severity=SEVERITY_INFO,
        call_id=123,
    )

    with session_scope() as session:
        record = session.query(AuditLog).order_by(AuditLog.id.desc()).first()

        assert record.event_type == EVENT_PIPELINE_STARTED
        assert record.message == "Pipeline started"
        assert record.severity == SEVERITY_INFO
        assert record.call_id == 123


def test_log_event_allows_missing_call_id():
    """Test that call_id can be omitted."""
    init_db()

    log_event(
        event_type=EVENT_PIPELINE_FAILED,
        message="Pipeline failed",
        severity=SEVERITY_ERROR,
    )

    with session_scope() as session:
        record = session.query(AuditLog).order_by(AuditLog.id.desc()).first()

        assert record.call_id is None


def test_log_event_rejects_invalid_event_type():
    """Test that unknown event types are rejected."""
    with pytest.raises(ValueError):
        log_event(
            event_type="unknown_event",
            message="Invalid event",
            severity=SEVERITY_INFO,
        )


def test_log_event_rejects_invalid_severity():
    """Test that unknown severity values are rejected."""
    with pytest.raises(ValueError):
        log_event(
            event_type=EVENT_PIPELINE_STARTED,
            message="Invalid severity",
            severity="debug",
        )
