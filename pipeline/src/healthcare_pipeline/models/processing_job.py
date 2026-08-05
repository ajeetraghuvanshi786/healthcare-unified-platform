from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from healthcare_pipeline.models.enums import ProcessingJobStatus, ProcessingStage

if TYPE_CHECKING:
    from healthcare_pipeline.models.ingestion_batch import IngestionBatch
    from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
    from healthcare_pipeline.models.tenant import Tenant


class ProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Track one idempotent processing attempt for one raw healthcare record."""

    __tablename__ = "processing_job"

    __table_args__ = (
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        CheckConstraint("max_attempts >= 1", name="max_attempts_positive"),
        CheckConstraint("attempt_number <= max_attempts", name="attempt_within_limit"),
        CheckConstraint("priority BETWEEN 0 AND 100", name="priority_range"),
        CheckConstraint(
            "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
            name="completion_after_start",
        ),
        UniqueConstraint(
            "tenant_id",
            "raw_ingestion_record_id",
            "stage",
            "attempt_number",
            name="tenant_record_stage_attempt",
        ),
        Index(
            "ix_processing_job_claim_queue",
            "status",
            "available_at",
            "priority",
            "created_at",
        ),
        Index(
            "ix_processing_job_tenant_status_stage",
            "tenant_id",
            "status",
            "stage",
        ),
        Index(
            "ix_processing_job_record_stage",
            "raw_ingestion_record_id",
            "stage",
        ),
        Index("ix_processing_job_correlation_id", "correlation_id"),
        Index("ix_processing_job_lease_expiry", "lease_expires_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ingestion_batch_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("ingestion_batch.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_ingestion_record_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("raw_ingestion_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parent_job_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("processing_job.id", ondelete="RESTRICT"),
        nullable=True,
    )
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[ProcessingStage] = mapped_column(
        Enum(
            ProcessingStage,
            name="processing_stage",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    status: Mapped[ProcessingJobStatus] = mapped_column(
        Enum(
            ProcessingJobStatus,
            name="processing_job_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ProcessingJobStatus.QUEUED,
        server_default=ProcessingJobStatus.QUEUED.value,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )
    max_attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=5, server_default="5"
    )
    priority: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=50, server_default="50"
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(String(150))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    processing_metrics: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    tenant: Mapped[Tenant] = relationship()
    ingestion_batch: Mapped[IngestionBatch] = relationship()
    raw_ingestion_record: Mapped[RawIngestionRecord] = relationship()
    parent_job: Mapped[ProcessingJob | None] = relationship(remote_side="ProcessingJob.id")
