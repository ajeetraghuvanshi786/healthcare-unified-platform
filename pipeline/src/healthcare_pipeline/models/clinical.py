from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from healthcare_pipeline.models.base import Base


def _clinical_message_fk(name: str) -> ForeignKey:
    return ForeignKey("clinical_messages.id", name=name, ondelete="CASCADE")


class ClinicalMessageRecord(Base):
    __tablename__ = "clinical_messages"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_message_id",
            name="uq_clinical_message_source",
        ),
        Index(
            "ix_clinical_message_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "received_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "master_patients.id",
            name="fk_clinical_messages_master_patient_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    source_message_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_format: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ClinicalEncounterRecord(Base):
    __tablename__ = "clinical_encounters"
    __table_args__ = (
        Index(
            "ix_clinical_encounter_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "start_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_encounters_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    encounter_class: Mapped[str] = mapped_column(String(32), nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_type: Mapped[str | None] = mapped_column(String(128))
    admission_type: Mapped[str | None] = mapped_column(String(128))
    discharge_disposition: Mapped[str | None] = mapped_column(String(128))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalDiagnosisRecord(Base):
    __tablename__ = "clinical_diagnoses"
    __table_args__ = (
        Index(
            "ix_clinical_diagnosis_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "recorded_at",
        ),
        Index("ix_clinical_diagnosis_code", "code_system", "code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_diagnoses_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code_system: Mapped[str | None] = mapped_column(String(256))
    code: Mapped[str | None] = mapped_column(String(128))
    display: Mapped[str | None] = mapped_column(String(512))
    diagnosis_type: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalObservationRecord(Base):
    __tablename__ = "clinical_observations"
    __table_args__ = (
        Index(
            "ix_clinical_observation_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "effective_at",
        ),
        Index("ix_clinical_observation_code", "code_system", "code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_observations_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    order_service_system: Mapped[str | None] = mapped_column(String(256))
    order_service_code: Mapped[str | None] = mapped_column(String(128))
    order_service_display: Mapped[str | None] = mapped_column(String(512))
    code_system: Mapped[str | None] = mapped_column(String(256))
    code: Mapped[str | None] = mapped_column(String(128))
    display: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False)
    values_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    unit_system: Mapped[str | None] = mapped_column(String(256))
    unit_code: Mapped[str | None] = mapped_column(String(128))
    unit_display: Mapped[str | None] = mapped_column(String(256))
    reference_range: Mapped[str | None] = mapped_column(String(512))
    abnormal_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalAllergyRecord(Base):
    __tablename__ = "clinical_allergies"
    __table_args__ = (
        Index(
            "ix_clinical_allergy_patient_date",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "identified_date",
        ),
        Index("ix_clinical_allergy_code", "allergen_system", "allergen_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_allergies_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    allergen_system: Mapped[str | None] = mapped_column(String(256))
    allergen_code: Mapped[str | None] = mapped_column(String(128))
    allergen_display: Mapped[str | None] = mapped_column(String(512))
    severity_display: Mapped[str | None] = mapped_column(String(256))
    reactions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    identified_date: Mapped[date | None] = mapped_column(Date)
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalMedicationOrderRecord(Base):
    __tablename__ = "clinical_medication_orders"
    __table_args__ = (
        Index(
            "ix_clinical_med_order_patient",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
        ),
        Index("ix_clinical_med_order_code", "medication_system", "medication_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_med_orders_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    medication_system: Mapped[str | None] = mapped_column(String(256))
    medication_code: Mapped[str | None] = mapped_column(String(128))
    medication_display: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str | None] = mapped_column(String(64))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalMedicationAdministrationRecord(Base):
    __tablename__ = "clinical_medication_administrations"
    __table_args__ = (
        Index(
            "ix_clinical_med_admin_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "start_at",
        ),
        Index("ix_clinical_med_admin_code", "medication_system", "medication_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_med_admins_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    medication_system: Mapped[str | None] = mapped_column(String(256))
    medication_code: Mapped[str | None] = mapped_column(String(128))
    medication_display: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str | None] = mapped_column(String(64))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalCoverageRecord(Base):
    __tablename__ = "clinical_coverages"
    __table_args__ = (
        Index(
            "ix_clinical_coverage_patient_dates",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "effective_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_coverages_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payer_name: Mapped[str | None] = mapped_column(String(512))
    group_number: Mapped[str | None] = mapped_column(String(256))
    effective_date: Mapped[date | None] = mapped_column(Date)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class ClinicalProvenanceRecord(Base):
    __tablename__ = "clinical_provenance"
    __table_args__ = (
        Index("ix_clinical_provenance_resource", "resource_type", "resource_id"),
        Index(
            "ix_clinical_provenance_source",
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_message_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_provenance_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    source_message_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ClinicalTimelineEventRecord(Base):
    __tablename__ = "clinical_timeline_events"
    __table_args__ = (
        Index(
            "ix_clinical_timeline_patient_time",
            "tenant_id",
            "identity_domain",
            "master_patient_id",
            "occurred_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    clinical_message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        _clinical_message_fk("fk_clinical_timeline_message_id"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_domain: Mapped[str] = mapped_column(String(128), nullable=False)
    master_patient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    display: Mapped[str] = mapped_column(String(512), nullable=False)
    details: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
