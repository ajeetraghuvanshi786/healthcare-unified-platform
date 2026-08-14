from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from healthcare_pipeline.models.base import Base


class MasterPatientModel(Base):
    __tablename__ = "master_patients"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_master_patients_scope", "tenant_id", "identity_domain", "id"),
    )
    __mapper_args__ = {"version_id_col": version}


class MasterPatientLinkModel(Base):
    __tablename__ = "master_patient_links"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    master_patient_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("master_patients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'unlinked')",
            name="master_link_status_valid",
        ),
        Index("ix_master_links_master_active", "master_patient_id", "status"),
        Index(
            "uq_master_links_active_source",
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_record_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )


class IdentityReviewCaseModel(Base):
    __tablename__ = "identity_review_cases"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_record_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    __table_args__ = (
        Index("ix_identity_reviews_scope_status", "tenant_id", "identity_domain", "status"),
    )
    __mapper_args__ = {"version_id_col": version}


class IdentityDecisionEventModel(Base):
    __tablename__ = "identity_decision_events"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    action: Mapped[str] = mapped_column(String(48), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("master_patients.id", ondelete="RESTRICT"),
        nullable=True,
    )
    review_case_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("identity_review_cases.id", ondelete="RESTRICT"),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_identity_events_master_time", "master_patient_id", "occurred_at"),
        Index("ix_identity_events_review_time", "review_case_id", "occurred_at"),
        Index("ix_identity_events_scope_time", "tenant_id", "identity_domain", "occurred_at"),
    )


class IdentitySourceRecordModel(Base):
    __tablename__ = "identity_source_records"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    encryption_key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_record_id",
            name="uq_identity_source_record_scope",
        ),
        Index("ix_identity_source_record_token", "source_record_id"),
    )


class IdentityCandidateKeyModel(Base):
    __tablename__ = "identity_candidate_keys"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    source_record_db_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("identity_source_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_record_db_id",
            "key_hash",
            name="uq_identity_candidate_record_key",
        ),
        Index("ix_identity_candidate_lookup", "tenant_id", "identity_domain", "key_hash"),
    )
