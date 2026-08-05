from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from healthcare_pipeline.models.enums import TransformationStatus

if TYPE_CHECKING:
    from healthcare_pipeline.models.processing_job import ProcessingJob
    from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
    from healthcare_pipeline.models.tenant import Tenant


class TransformationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Record each ordered transformation for replay and data-lineage analysis."""

    __tablename__ = "transformation_log"

    __table_args__ = (
        CheckConstraint("sequence_number >= 0", name="sequence_number_non_negative"),
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0", name="duration_non_negative"
        ),
        CheckConstraint(
            "input_hash IS NULL OR char_length(input_hash) = 64",
            name="input_hash_sha256_length",
        ),
        CheckConstraint(
            "output_hash IS NULL OR char_length(output_hash) = 64",
            name="output_hash_sha256_length",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="completion_after_start",
        ),
        UniqueConstraint(
            "processing_job_id",
            "sequence_number",
            name="job_sequence_number",
        ),
        Index(
            "ix_transformation_log_record_sequence",
            "raw_ingestion_record_id",
            "sequence_number",
        ),
        Index(
            "ix_transformation_log_job_status",
            "processing_job_id",
            "status",
        ),
        Index(
            "ix_transformation_log_tenant_name",
            "tenant_id",
            "transformation_name",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    processing_job_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("processing_job.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    raw_ingestion_record_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("raw_ingestion_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    transformation_name: Mapped[str] = mapped_column(String(200), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[TransformationStatus] = mapped_column(
        Enum(
            TransformationStatus,
            name="transformation_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=TransformationStatus.STARTED,
        server_default=TransformationStatus.STARTED.value,
    )
    input_hash: Mapped[str | None] = mapped_column(String(64))
    output_hash: Mapped[str | None] = mapped_column(String(64))
    input_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    output_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    output_reference: Mapped[str | None] = mapped_column(String(500))
    details: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    tenant: Mapped[Tenant] = relationship()
    processing_job: Mapped[ProcessingJob] = relationship()
    raw_ingestion_record: Mapped[RawIngestionRecord] = relationship()
