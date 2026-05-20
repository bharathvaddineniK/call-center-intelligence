from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import config
from src.database.models import Base

engine = create_engine(f"sqlite:///{config.DATABASE_PATH}")
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(engine)
    _ensure_call_status_column()
    _ensure_caller_id_column()
    _ensure_department_column()
    _ensure_report_json_column()
    _ensure_compliance_severity_column()
    _ensure_violation_description_column()
    _ensure_timestamp_evidence_column()


def _ensure_call_status_column() -> None:
    """Add call_records.status for existing SQLite databases."""
    _ensure_column(
        table_name="call_records",
        column_name="status",
        column_definition="VARCHAR(20) NOT NULL DEFAULT 'completed'",
    )


def _ensure_report_json_column() -> None:
    """Add reports.report_json for existing SQLite databases."""
    _ensure_column(
        table_name="reports",
        column_name="report_json",
        column_definition="TEXT",
    )


def _ensure_compliance_severity_column() -> None:
    """Add reports.compliance_severity for existing SQLite databases."""
    _ensure_column(
        table_name="reports",
        column_name="compliance_severity",
        column_definition="VARCHAR(20)",
    )


def _ensure_violation_description_column() -> None:
    """Add reports.violation_description for existing SQLite databases."""
    _ensure_column(
        table_name="reports",
        column_name="violation_description",
        column_definition="TEXT",
    )


def _ensure_timestamp_evidence_column() -> None:
    """Add reports.timestamp_evidence for existing SQLite databases."""
    _ensure_column(
        table_name="reports",
        column_name="timestamp_evidence",
        column_definition="JSON",
    )


def _ensure_caller_id_column() -> None:
    """Add call_records.caller_id for existing SQLite databases."""
    _ensure_column(
        table_name="call_records",
        column_name="caller_id",
        column_definition="VARCHAR(100)",
    )


def _ensure_department_column() -> None:
    """Add call_records.department for existing SQLite databases."""
    _ensure_column(
        table_name="call_records",
        column_name="department",
        column_definition="VARCHAR(100)",
    )


def _ensure_column(
    *,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    """Add a column when an existing SQLite database predates it."""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        )
