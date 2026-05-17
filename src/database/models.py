from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Call(Base):
    __tablename__ = "call_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    duration: Mapped[float] = mapped_column(Float)
    transcription: Mapped[str] = mapped_column(Text)
    speaker_count: Mapped[int] = mapped_column(Integer)
    sentiment: Mapped[str] = mapped_column(String(20))
    call_purpose: Mapped[str | None] = mapped_column(String(500), nullable=True)
    agent_behavior: Mapped[str | None] = mapped_column(String(500), nullable=True)
    segments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("call_records.id"), unique=True)
    overall_score: Mapped[float] = mapped_column(Float)
    empathy_score: Mapped[float] = mapped_column(Float)
    resolution_score: Mapped[float] = mapped_column(Float)
    compliance_score: Mapped[float] = mapped_column(Float)
    communication_score: Mapped[float] = mapped_column(Float)
    professionalism_score: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    compliance_flag: Mapped[bool] = mapped_column(Boolean)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[int | None] = mapped_column(
        ForeignKey("call_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )


class TranscriptionCache(Base):
    __tablename__ = "transcription_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    text: Mapped[str] = mapped_column(Text)
    segments: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC)
    )
