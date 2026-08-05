from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from healthcare_pipeline.models.enums import DeadLetterStatus, ErrorRecoverability

if TYPE_CHECKING:
    from healthcare_pipeline.models.processing_job import ProcessingJob
    from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
    from healthcare_pipeline.models.tenant import Tenant


class DeadLetterRecord(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Track a failed record requiring retry, remediation, or disposal."""

    __tablename__ = "dead_letter_record"

    __table_args__ = (
        CheckConstraint("failure_count >= 1", name="failure_count_positive"),
        CheckConstraint(
            "last_failed_at >= first_failed_at", name="last_failure_after_first"
        ),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= first_failed_at",
            name="resolution_after_failure",
        ),
        Index(
            "ix_dead_letter_record_work_queue",
            "status",
            "next_retry_at",
            "last_failed_at",
        ),
        Index(
            "ix_dead_letter_record_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_dead_letter_record_raw_record",
            "raw_ingestion_record_id",
            "status",
        ),
        Index("ix_dead_letter_record_error_code", "error_code"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_ingestion_record_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("raw_ingestion_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    processing_job_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("processing_job.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[DeadLetterStatus] = mapped_column(
        Enum(
            DeadLetterStatus,
            name="dead_letter_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=DeadLetterStatus.OPEN,
        server_default=DeadLetterStatus.OPEN.value,
        index=True,
    )
    recoverability: Mapped[ErrorRecoverability] = mapped_column(
        Enum(
            ErrorRecoverability,
            name="error_recoverability",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ErrorRecoverability.UNKNOWN,
        server_default=ErrorRecoverability.UNKNOWN.value,
    )
    error_category: Mapped[str] = mapped_column(String(100), nullable=False)
    error_code: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    failure_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    first_failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_code: Mapped[str | None] = mapped_column(String(100))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    diagnostic_context: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    tenant: Mapped[Tenant] = relationship()
    raw_ingestion_record: Mapped[RawIngestionRecord] = relationship()
    processing_job: Mapped[ProcessingJob | None] = relationship()
