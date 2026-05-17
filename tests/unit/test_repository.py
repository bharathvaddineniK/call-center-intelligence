from src.database.repository import (
    get_all_calls,
    get_call_by_id,
    get_recent_audit_logs,
    get_report_by_call_id,
    save_call,
    save_report,
)
from src.services.security.audit_logger import (
    EVENT_PIPELINE_FAILED,
    EVENT_PIPELINE_STARTED,
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
    )

    assert isinstance(report_id, int)
    assert report_id > 0


def test_get_call_by_id_returns_correct_call():
    """Save a call, retrieve it by id, and verify the filename."""
    call_id = create_test_call(filename="billing-call.mp3", file_hash="hash456")

    call = get_call_by_id(call_id)

    assert call.filename == "billing-call.mp3"


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
    )

    report = get_report_by_call_id(call_id)

    assert report.call_id == call_id
    assert report.summary == "The agent helped the caller."


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
    )

    report = get_report_by_call_id(call_id)

    assert second_report_id == first_report_id
    assert report.overall_score == 70.0
    assert report.summary == "The updated report summary."
    assert report.pdf_path == "reports/new-call.pdf"


def test_get_recent_audit_logs():
    """Save audit logs and return the most recent entries."""
    log_event(
        event_type=EVENT_PIPELINE_STARTED,
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
