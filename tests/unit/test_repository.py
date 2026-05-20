from src.database.models import (
    CALL_STATUS_COMPLETED,
    CALL_STATUS_FAILED,
    CALL_STATUS_FLAGGED,
)
from src.database.repository import (
    get_all_calls,
    get_call_by_id,
    get_call_status_counts,
    get_recent_audit_logs,
    get_report_by_call_id,
    get_table_counts,
    save_call,
    save_failed_call,
    save_report,
    update_call_metadata,
    update_call_status,
)
from src.services.security.audit_logger import (
    EVENT_INTAKE_VALIDATED,
    EVENT_PIPELINE_FAILED,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    log_event,
)


def create_test_call(filename: str = "call.mp3", file_hash: str = "hash123") -> int:
    """Save a simple call for repository tests."""
    return save_call(
        filename=filename,
        file_hash=file_hash,
        duration=60.0,
        transcription="Agent: Hello. Caller: I need help.",
        speaker_count=2,
        sentiment="neutral",
        call_purpose="support",
    )


def test_save_call_returns_id():
    """Save a call and return its database id."""
    call_id = create_test_call()

    assert isinstance(call_id, int)
    assert call_id > 0


def test_save_report_returns_id():
    """Save a report linked to a call and return its database id."""
    call_id = create_test_call()

    report_id = save_report(
        call_id=call_id,
        overall_score=85.0,
        empathy_score=90.0,
        resolution_score=80.0,
        compliance_score=85.0,
        communication_score=88.0,
        professionalism_score=92.0,
        summary="The agent helped the caller.",
        compliance_flag=True,
        pdf_path="reports/call.pdf",
        report_json='{"summary": "The agent helped the caller."}',
        compliance_severity="low",
        violation_description="Minor disclosure gap",
        timestamp_evidence=["00:10"],
    )

    assert isinstance(report_id, int)
    assert report_id > 0

    report = get_report_by_call_id(call_id)
    assert report.report_json == '{"summary": "The agent helped the caller."}'
    assert report.compliance_severity == "low"
    assert report.violation_description == "Minor disclosure gap"
    assert report.timestamp_evidence == ["00:10"]


def test_get_call_by_id_returns_correct_call():
    """Save a call, retrieve it by id, and verify the filename."""
    call_id = create_test_call(filename="billing-call.mp3", file_hash="hash456")

    call = get_call_by_id(call_id)

    assert call.filename == "billing-call.mp3"
    assert call.status == CALL_STATUS_COMPLETED


def test_save_call_persists_optional_metadata():
    """Save optional caller metadata on a completed call."""
    call_id = save_call(
        filename="metadata-call.mp3",
        file_hash="metadata-hash",
        duration=60.0,
        transcription="Agent: Hello. Caller: I need help.",
        speaker_count=2,
        sentiment="neutral",
        call_purpose="support",
        caller_id="[REDACTED_EMAIL]",
        department="Support",
    )

    call = get_call_by_id(call_id)

    assert call.caller_id == "[REDACTED_EMAIL]"
    assert call.department == "Support"


def test_save_call_accepts_status():
    """Save a call with an explicit status."""
    call_id = create_test_call(filename="flagged-call.mp3", file_hash="hash-flagged")
    update_call_status(call_id, CALL_STATUS_FLAGGED)

    call = get_call_by_id(call_id)

    assert call.status == CALL_STATUS_FLAGGED


def test_save_failed_call_persists_minimal_failed_row():
    """Persist a minimal failed call row when the pipeline stops before reports."""
    call_id = save_failed_call(
        audio_path="fake/path.wav",
        file_hash=None,
        error="File not found",
        status=CALL_STATUS_FAILED,
    )

    call = get_call_by_id(call_id)

    assert call.filename == "path.wav"
    assert call.status == CALL_STATUS_FAILED
    assert call.transcription == ""
    assert call.agent_behavior == "File not found"


def test_save_failed_call_persists_optional_metadata():
    """Persist redacted metadata on failed or blocked call rows."""
    call_id = save_failed_call(
        audio_path="fake/path.wav",
        file_hash=None,
        error="File not found",
        status=CALL_STATUS_FAILED,
        caller_id="[REDACTED_PHONE]",
        department="Dispatch",
    )

    call = get_call_by_id(call_id)

    assert call.caller_id == "[REDACTED_PHONE]"
    assert call.department == "Dispatch"


def test_update_call_metadata():
    """Update caller metadata for an existing call row."""
    call_id = create_test_call(filename="update-metadata.mp3", file_hash="metadata-update")

    update_call_metadata(
        call_id,
        caller_id="[REDACTED_EMAIL]",
        department="Emergency Dispatch",
    )

    call = get_call_by_id(call_id)

    assert call.caller_id == "[REDACTED_EMAIL]"
    assert call.department == "Emergency Dispatch"


def test_get_call_status_counts():
    """Return grouped call counts by status."""
    create_test_call(filename="completed-call.mp3", file_hash="status-completed")
    failed_call_id = save_failed_call(
        audio_path="failed/path.wav",
        file_hash=None,
        error="File not found",
        status=CALL_STATUS_FAILED,
    )
    update_call_status(failed_call_id, CALL_STATUS_FLAGGED)

    counts = get_call_status_counts()

    assert counts[CALL_STATUS_COMPLETED] == 1
    assert counts[CALL_STATUS_FLAGGED] == 1
    assert CALL_STATUS_FAILED not in counts


def test_get_all_calls_returns_list():
    """Save two calls and return them as a list."""
    create_test_call(filename="first-call.mp3", file_hash="hash111")
    create_test_call(filename="second-call.mp3", file_hash="hash222")

    calls = get_all_calls()

    assert isinstance(calls, list)
    assert len(calls) == 2


def test_get_report_by_call_id():
    """Save a report and retrieve it by call id."""
    call_id = create_test_call()

    save_report(
        call_id=call_id,
        overall_score=85.0,
        empathy_score=90.0,
        resolution_score=80.0,
        compliance_score=85.0,
        communication_score=88.0,
        professionalism_score=92.0,
        summary="The agent helped the caller.",
        compliance_flag=True,
        pdf_path="reports/call.pdf",
        compliance_severity="none",
        violation_description="No violation detected",
        timestamp_evidence=[],
    )

    report = get_report_by_call_id(call_id)

    assert report.call_id == call_id
    assert report.summary == "The agent helped the caller."
    assert report.compliance_severity == "none"


def test_save_report_updates_existing_report_for_call():
    """Save a second report for the same call by updating the existing row."""
    call_id = create_test_call()

    first_report_id = save_report(
        call_id=call_id,
        overall_score=85.0,
        empathy_score=90.0,
        resolution_score=80.0,
        compliance_score=85.0,
        communication_score=88.0,
        professionalism_score=92.0,
        summary="The agent helped the caller.",
        compliance_flag=True,
        pdf_path="reports/old-call.pdf",
        report_json='{"version": 1}',
        compliance_severity="low",
        violation_description="Old issue",
        timestamp_evidence=["00:01"],
    )
    second_report_id = save_report(
        call_id=call_id,
        overall_score=70.0,
        empathy_score=75.0,
        resolution_score=65.0,
        compliance_score=80.0,
        communication_score=70.0,
        professionalism_score=72.0,
        summary="The updated report summary.",
        compliance_flag=False,
        pdf_path="reports/new-call.pdf",
        report_json='{"version": 2}',
        compliance_severity="none",
        violation_description="No violation detected",
        timestamp_evidence=[],
    )

    report = get_report_by_call_id(call_id)

    assert second_report_id == first_report_id
    assert report.overall_score == 70.0
    assert report.summary == "The updated report summary."
    assert report.pdf_path == "reports/new-call.pdf"
    assert report.report_json == '{"version": 2}'
    assert report.compliance_severity == "none"
    assert report.violation_description == "No violation detected"
    assert report.timestamp_evidence == []


def test_get_recent_audit_logs():
    """Save audit logs and return the most recent entries."""
    log_event(
        event_type=EVENT_INTAKE_VALIDATED,
        message="Pipeline started",
        severity=SEVERITY_INFO,
    )
    log_event(
        event_type=EVENT_PIPELINE_FAILED,
        message="Pipeline failed",
        severity=SEVERITY_ERROR,
    )

    audit_logs = get_recent_audit_logs()

    assert isinstance(audit_logs, list)
    assert len(audit_logs) == 2
    assert audit_logs[0].message == "Pipeline failed"


def test_get_table_counts():
    """Return storage diagnostic row counts."""
    create_test_call()

    counts = get_table_counts()

    assert counts["calls"] == 1
    assert counts["reports"] == 0
    assert counts["audit_logs"] == 0
