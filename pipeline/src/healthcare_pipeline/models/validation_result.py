from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from healthcare_pipeline.models.enums import (
    ValidationCategory,
    ValidationOutcome,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from healthcare_pipeline.models.processing_job import ProcessingJob
    from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
    from healthcare_pipeline.models.tenant import Tenant


class ValidationResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one immutable validation rule outcome with traceable context."""

    __tablename__ = "validation_result"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(rule_code)) >= 1", name="rule_code_not_blank"
        ),
        CheckConstraint("char_length(trim(message)) >= 1", name="message_not_blank"),
        Index(
            "ix_validation_result_job_outcome",
            "processing_job_id",
            "outcome",
            "severity",
        ),
        Index(
            "ix_validation_result_record_category",
            "raw_ingestion_record_id",
            "category",
        ),
        Index(
            "ix_validation_result_tenant_validated",
            "tenant_id",
            "validated_at",
        ),
        Index("ix_validation_result_rule_code", "rule_code"),
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
    category: Mapped[ValidationCategory] = mapped_column(
        Enum(
            ValidationCategory,
            name="validation_category",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    outcome: Mapped[ValidationOutcome] = mapped_column(
        Enum(
            ValidationOutcome,
            name="validation_outcome",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    severity: Mapped[ValidationSeverity] = mapped_column(
        Enum(
            ValidationSeverity,
            name="validation_severity",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(String(150), nullable=False)
    rule_version: Mapped[str | None] = mapped_column(String(50))
    field_path: Mapped[str | None] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tenant: Mapped[Tenant] = relationship()
    processing_job: Mapped[ProcessingJob] = relationship()
    raw_ingestion_record: Mapped[RawIngestionRecord] = relationship()
