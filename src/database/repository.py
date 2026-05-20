import hashlib
from pathlib import Path

from sqlalchemy import func

from src.database.models import (
    CALL_STATUS_COMPLETED,
    CALL_STATUSES,
    AuditLog,
    Call,
    Report,
)
from src.database.session import session_scope


def get_call_by_hash(file_hash: str) -> Call | None:
    """Return a call record by file hash."""
    with session_scope() as session:
        call = session.query(Call).filter(Call.file_hash == file_hash).first()
        if call:
            session.expunge(call)
        return call


def save_call(
    *,
    filename: str,
    file_hash: str,
    duration: float,
    transcription: str,
    speaker_count: int,
    sentiment: str,
    call_purpose: str | None = None,
    agent_behavior: str | None = None,
    status: str = CALL_STATUS_COMPLETED,
    segments: dict | None = None,
    confidence: float | None = None,
    caller_id: str | None = None,
    department: str | None = None,
) -> int:
    """Save a call record and return the new call id."""
    _validate_call_status(status)

    call = Call(
        filename=filename,
        file_hash=file_hash,
        duration=duration,
        transcription=transcription,
        speaker_count=speaker_count,
        sentiment=sentiment,
        call_purpose=call_purpose,
        agent_behavior=agent_behavior,
        status=status,
        segments=segments,
        confidence=confidence,
        caller_id=caller_id,
        department=department,
    )

    with session_scope() as session:
        session.add(call)
        session.flush()
        session.refresh(call)
        return call.id


def save_failed_call(
    *,
    audio_path: str | None,
    file_hash: str | None,
    error: str | None,
    status: str,
    transcript: str | None = None,
    duration: float | None = None,
    speaker_count: int | None = None,
    segments: dict | None = None,
    confidence: float | None = None,
    caller_id: str | None = None,
    department: str | None = None,
) -> int:
    """Persist a minimal call row for failed or blocked pipeline runs."""
    _validate_call_status(status)
    resolved_hash = file_hash or _fallback_file_hash(audio_path, error, status)
    existing_call = get_call_by_hash(resolved_hash)

    if existing_call is not None:
        update_call_status(existing_call.id, status)
        update_call_metadata(
            existing_call.id,
            caller_id=caller_id,
            department=department,
        )
        return existing_call.id

    return save_call(
        filename=Path(audio_path).name if audio_path else "unknown",
        file_hash=resolved_hash,
        duration=duration or 0,
        transcription=transcript or "",
        speaker_count=speaker_count or 0,
        sentiment="unknown",
        call_purpose=status,
        agent_behavior=error or status,
        status=status,
        segments=segments,
        confidence=confidence,
        caller_id=caller_id,
        department=department,
    )


def _fallback_file_hash(audio_path: str | None, error: str | None, status: str) -> str:
    """Build a deterministic synthetic hash when audio hashing never completed."""
    key = f"{audio_path or 'unknown'}:{error or ''}:{status}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def update_call_status(call_id: int, status: str) -> None:
    """Update the persisted status for a call record."""
    _validate_call_status(status)

    with session_scope() as session:
        call = session.query(Call).filter(Call.id == call_id).first()
        if call is not None:
            call.status = status


def update_call_metadata(
    call_id: int,
    *,
    caller_id: str | None = None,
    department: str | None = None,
) -> None:
    """Update optional caller metadata for an existing call record."""
    with session_scope() as session:
        call = session.query(Call).filter(Call.id == call_id).first()
        if call is None:
            return

        call.caller_id = caller_id
        call.department = department


def _validate_call_status(status: str) -> None:
    """Raise a clear error for unsupported call statuses."""
    if status not in CALL_STATUSES:
        valid_statuses = ", ".join(sorted(CALL_STATUSES))
        raise ValueError(f"Invalid call status '{status}'. Use one of: {valid_statuses}.")


def save_report(
    call_id: int,
    overall_score: float,
    empathy_score: float,
    resolution_score: float,
    compliance_score: float,
    communication_score: float,
    professionalism_score: float,
    summary: str,
    compliance_flag: bool,
    pdf_path: str,
    report_json: str | None = None,
    compliance_severity: str | None = None,
    violation_description: str | None = None,
    timestamp_evidence: list[str] | None = None,
) -> int:
    """Save or update a report record and return the report id."""

    with session_scope() as session:
        report = session.query(Report).filter(Report.call_id == call_id).first()

        if report is None:
            report = Report(call_id=call_id)
            session.add(report)

        report.overall_score = overall_score
        report.empathy_score = empathy_score
        report.resolution_score = resolution_score
        report.compliance_score = compliance_score
        report.communication_score = communication_score
        report.professionalism_score = professionalism_score
        report.summary = summary
        report.compliance_flag = compliance_flag
        report.compliance_severity = compliance_severity
        report.violation_description = violation_description
        report.timestamp_evidence = timestamp_evidence
        report.pdf_path = pdf_path
        report.report_json = report_json

        session.flush()
        session.refresh(report)
        return report.id


def get_call_by_id(call_id: int) -> Call | None:
    """Return a call record by id."""

    with session_scope() as session:
        call = session.query(Call).filter(Call.id == call_id).first()
        if call is not None:
            session.expunge(call)
        return call


def get_all_calls(limit: int = 20) -> list[Call]:
    """Return the most recent calls ordered by created_at descending."""

    with session_scope() as session:
        calls = session.query(Call).order_by(Call.created_at.desc()).limit(limit).all()
        for call in calls:
            session.expunge(call)
        return calls


def get_report_by_call_id(call_id: int) -> Report | None:
    """Return a report record by call id."""
    with session_scope() as session:
        report = (
            session.query(Report)
            .filter(Report.call_id == call_id)
            .order_by(Report.id.desc())
            .first()
        )
        if report is not None:
            session.expunge(report)
        return report


def get_recent_audit_logs(limit: int = 20) -> list[AuditLog]:
    """Return the most recent audit log entries."""
    with session_scope() as session:
        audit_logs = (
            session.query(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
            .all()
        )
        for audit_log in audit_logs:
            session.expunge(audit_log)
        return audit_logs


def get_table_counts() -> dict[str, int]:
    """Return row counts for observability storage diagnostics."""
    with session_scope() as session:
        return {
            "calls": session.query(Call).count(),
            "reports": session.query(Report).count(),
            "audit_logs": session.query(AuditLog).count(),
        }


def get_call_status_counts() -> dict[str, int]:
    """Return count of calls grouped by status."""
    with session_scope() as session:
        rows = session.query(Call.status, func.count(Call.id)).group_by(Call.status).all()
        return {status: count for status, count in rows}
