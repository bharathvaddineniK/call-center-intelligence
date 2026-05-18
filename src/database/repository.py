from src.database.models import AuditLog, Call, Report
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
    segments: dict | None = None,
    confidence: float | None = None,
) -> int:
    """Save a call record and return the new call id."""
    call = Call(
        filename=filename,
        file_hash=file_hash,
        duration=duration,
        transcription=transcription,
        speaker_count=speaker_count,
        sentiment=sentiment,
        call_purpose=call_purpose,
        agent_behavior=agent_behavior,
        segments=segments,
        confidence=confidence,
    )

    with session_scope() as session:
        session.add(call)
        session.flush()
        session.refresh(call)
        return call.id


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
        report.pdf_path = pdf_path

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
