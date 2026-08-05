from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from healthcare_pipeline.models.enums import CheckpointStatus, ProcessingStage

if TYPE_CHECKING:
    from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
    from healthcare_pipeline.models.source_system import SourceSystem
    from healthcare_pipeline.models.tenant import Tenant


class ProcessingCheckpoint(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Persist resumable progress for a source, stage, and logical partition."""

    __tablename__ = "processing_checkpoint"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(partition_key)) >= 1", name="partition_key_not_blank"
        ),
        CheckConstraint(
            "char_length(trim(checkpoint_value)) >= 1",
            name="checkpoint_value_not_blank",
        ),
        UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "stage",
            "partition_key",
            name="tenant_source_stage_partition",
        ),
        Index(
            "ix_processing_checkpoint_tenant_stage",
            "tenant_id",
            "stage",
            "status",
        ),
        Index(
            "ix_processing_checkpoint_source_partition",
            "source_system_id",
            "partition_key",
        ),
        Index("ix_processing_checkpoint_lease_expiry", "lease_expires_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_system_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("source_system.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    last_processed_record_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("raw_ingestion_record.id", ondelete="SET NULL"),
        nullable=True,
    )
    stage: Mapped[ProcessingStage] = mapped_column(
        Enum(
            ProcessingStage,
            name="processing_stage",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    partition_key: Mapped[str] = mapped_column(String(255), nullable=False)
    checkpoint_value: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[CheckpointStatus] = mapped_column(
        Enum(
            CheckpointStatus,
            name="checkpoint_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=CheckpointStatus.ACTIVE,
        server_default=CheckpointStatus.ACTIVE.value,
        index=True,
    )
    watermark_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(150))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checkpoint_metadata: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    tenant: Mapped[Tenant] = relationship()
    source_system: Mapped[SourceSystem] = relationship()
    last_processed_record: Mapped[RawIngestionRecord | None] = relationship()
