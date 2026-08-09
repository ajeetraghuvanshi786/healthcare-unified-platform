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
    LargeBinary,
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
)
from healthcare_pipeline.models.enums import (
    CompressionType,
    PayloadEncoding,
    RawRecordStatus,
)

if TYPE_CHECKING:
    from healthcare_pipeline.models.ingestion_batch import IngestionBatch
    from healthcare_pipeline.models.source_system import SourceSystem
    from healthcare_pipeline.models.tenant import Tenant


class RawIngestionRecord(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Preserve the exact source payload and its ingestion metadata.

    The payload and its integrity metadata are immutable after creation.
    """

    __tablename__ = "raw_ingestion_record"

    __table_args__ = (
        CheckConstraint(
            "char_length(payload_hash) = 64",
            name="sha256_hash_length",
        ),
        CheckConstraint(
            "payload_size_bytes >= 0",
            name="payload_size_non_negative",
        ),
        CheckConstraint(
            "sequence_number IS NULL OR sequence_number >= 0",
            name="sequence_number_non_negative",
        ),
        UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "idempotency_key",
            name="tenant_source_idempotency_key",
        ),
        Index(
            "ix_raw_ingestion_record_hash_lookup",
            "tenant_id",
            "source_system_id",
            "payload_hash",
        ),
        Index(
            "ix_raw_ingestion_record_batch_status",
            "ingestion_batch_id",
            "status",
        ),
        Index(
            "ix_raw_ingestion_record_tenant_status_received",
            "tenant_id",
            "status",
            "received_at",
        ),
        Index(
            "ix_raw_ingestion_record_source_message_id",
            "source_system_id",
            "source_message_id",
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

    ingestion_batch_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "ingestion_batch.id",
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

    duplicate_of_record_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "raw_ingestion_record.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sequence_number: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    payload_encoding: Mapped[PayloadEncoding] = mapped_column(
        Enum(
            PayloadEncoding,
            name="payload_encoding",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=PayloadEncoding.UTF_8,
        server_default=PayloadEncoding.UTF_8.value,
    )

    compression_type: Mapped[CompressionType] = mapped_column(
        Enum(
            CompressionType,
            name="compression_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=CompressionType.NONE,
        server_default=CompressionType.NONE.value,
    )

    payload: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    payload_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    status: Mapped[RawRecordStatus] = mapped_column(
        Enum(
            RawRecordStatus,
            name="raw_record_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=RawRecordStatus.RECEIVED,
        server_default=RawRecordStatus.RECEIVED.value,
        index=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    transport_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tenant: Mapped[Tenant] = relationship()

    ingestion_batch: Mapped[IngestionBatch] = relationship(
        back_populates="raw_records",
    )

    source_system: Mapped[SourceSystem] = relationship()

    duplicate_of_record: Mapped[RawIngestionRecord | None] = relationship(
        remote_side="RawIngestionRecord.id",
    )