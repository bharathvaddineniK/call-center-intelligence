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


def _ensure_call_status_column() -> None:
    """Add call_records.status for existing SQLite databases."""
    inspector = inspect(engine)
    if "call_records" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("call_records")}
    if "status" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE call_records "
                "ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completed'"
            )
        )


def _ensure_caller_id_column() -> None:
    """Add call_records.caller_id for existing SQLite databases."""
    _ensure_nullable_call_records_column("caller_id", "VARCHAR(100)")


def _ensure_department_column() -> None:
    """Add call_records.department for existing SQLite databases."""
    _ensure_nullable_call_records_column("department", "VARCHAR(100)")


def _ensure_nullable_call_records_column(column_name: str, column_type: str) -> None:
    """Add an optional call_records column when an existing DB predates it."""
    inspector = inspect(engine)
    if "call_records" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("call_records")}
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(f"ALTER TABLE call_records ADD COLUMN {column_name} {column_type}")
        )
