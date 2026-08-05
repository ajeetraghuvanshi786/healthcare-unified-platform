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
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from healthcare_pipeline.models.enums import (
    DataStandard,
    IngestionBatchStatus,
    IngestionTransport,
)

if TYPE_CHECKING:
    from healthcare_pipeline.models.raw_ingestion_record import (
        RawIngestionRecord,
    )
    from healthcare_pipeline.models.source_system import SourceSystem
    from healthcare_pipeline.models.tenant import Tenant


class IngestionBatch(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """
    Represent one logical healthcare data delivery or import operation.

    A batch may contain one record or many thousands of records.
    """

    __tablename__ = "ingestion_batch"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(batch_reference)) >= 1",
            name="batch_reference_not_blank",
        ),
        CheckConstraint(
            "expected_record_count IS NULL "
            "OR expected_record_count >= 0",
            name="expected_record_count_non_negative",
        ),
        CheckConstraint(
            "received_record_count >= 0",
            name="received_record_count_non_negative",
        ),
        CheckConstraint(
            "processed_record_count >= 0",
            name="processed_record_count_non_negative",
        ),
        CheckConstraint(
            "failed_record_count >= 0",
            name="failed_record_count_non_negative",
        ),
        CheckConstraint(
            "total_payload_bytes >= 0",
            name="total_payload_bytes_non_negative",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="completion_after_start",
        ),
        UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "batch_reference",
            name="tenant_source_batch_reference",
        ),
        Index(
            "ix_ingestion_batch_tenant_status_created",
            "tenant_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_ingestion_batch_source_status",
            "source_system_id",
            "status",
        ),
        Index(
            "ix_ingestion_batch_correlation_id",
            "correlation_id",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "tenant.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    source_system_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "source_system.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    batch_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    correlation_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    transport: Mapped[IngestionTransport] = mapped_column(
        Enum(
            IngestionTransport,
            name="ingestion_transport",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    data_standard: Mapped[DataStandard] = mapped_column(
        Enum(
            DataStandard,
            name="ingestion_data_standard",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    standard_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[IngestionBatchStatus] = mapped_column(
        Enum(
            IngestionBatchStatus,
            name="ingestion_batch_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=IngestionBatchStatus.RECEIVING,
        server_default=IngestionBatchStatus.RECEIVING.value,
        index=True,
    )

    expected_record_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    received_record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    processed_record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    failed_record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    total_payload_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    source_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tenant: Mapped[Tenant] = relationship()

    source_system: Mapped[SourceSystem] = relationship()

    raw_records: Mapped[list[RawIngestionRecord]] = relationship(
        back_populates="ingestion_batch",
        cascade="save-update, merge",
    )