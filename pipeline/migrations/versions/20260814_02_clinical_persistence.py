"""add longitudinal clinical persistence, provenance and timeline read model

Revision ID: 20260814_02
Revises: 20260811_01
Create Date: 2026-08-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260814_02"
down_revision: str | None = "20260811_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def _scope_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("master_patient_id", UUID, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "clinical_messages",
        sa.Column("id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("source_message_id", sa.String(256), nullable=False),
        sa.Column("source_event_code", sa.String(64), nullable=False),
        sa.Column("source_format", sa.String(32), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["master_patient_id"],
            ["master_patients.id"],
            name="fk_clinical_messages_master_patient_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_messages"),
        sa.UniqueConstraint(
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_message_id",
            name="uq_clinical_message_source",
        ),
    )
    op.create_index(
        "ix_clinical_message_patient_time",
        "clinical_messages",
        ["tenant_id", "identity_domain", "master_patient_id", "received_at"],
    )

    op.create_table(
        "clinical_encounters",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("encounter_class", sa.String(32), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("service_type", sa.String(128), nullable=True),
        sa.Column("admission_type", sa.String(128), nullable=True),
        sa.Column("discharge_disposition", sa.String(128), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_encounters_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_encounters"),
    )
    op.create_index(
        "ix_clinical_encounter_patient_time",
        "clinical_encounters",
        ["tenant_id", "identity_domain", "master_patient_id", "start_at"],
    )

    op.create_table(
        "clinical_diagnoses",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("code_system", sa.String(256), nullable=True),
        sa.Column("code", sa.String(128), nullable=True),
        sa.Column("display", sa.String(512), nullable=True),
        sa.Column("diagnosis_type", sa.String(128), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_diagnoses_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_diagnoses"),
    )
    op.create_index(
        "ix_clinical_diagnosis_patient_time",
        "clinical_diagnoses",
        ["tenant_id", "identity_domain", "master_patient_id", "recorded_at"],
    )
    op.create_index(
        "ix_clinical_diagnosis_code",
        "clinical_diagnoses",
        ["code_system", "code"],
    )

    op.create_table(
        "clinical_observations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("order_service_system", sa.String(256), nullable=True),
        sa.Column("order_service_code", sa.String(128), nullable=True),
        sa.Column("order_service_display", sa.String(512), nullable=True),
        sa.Column("code_system", sa.String(256), nullable=True),
        sa.Column("code", sa.String(128), nullable=True),
        sa.Column("display", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("value_type", sa.String(32), nullable=False),
        sa.Column("values_json", sa.JSON(), nullable=False),
        sa.Column("unit_system", sa.String(256), nullable=True),
        sa.Column("unit_code", sa.String(128), nullable=True),
        sa.Column("unit_display", sa.String(256), nullable=True),
        sa.Column("reference_range", sa.String(512), nullable=True),
        sa.Column("abnormal_flags", sa.JSON(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_observations_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_observations"),
    )
    op.create_index(
        "ix_clinical_observation_patient_time",
        "clinical_observations",
        ["tenant_id", "identity_domain", "master_patient_id", "effective_at"],
    )
    op.create_index(
        "ix_clinical_observation_code",
        "clinical_observations",
        ["code_system", "code"],
    )

    op.create_table(
        "clinical_allergies",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("allergen_system", sa.String(256), nullable=True),
        sa.Column("allergen_code", sa.String(128), nullable=True),
        sa.Column("allergen_display", sa.String(512), nullable=True),
        sa.Column("severity_display", sa.String(256), nullable=True),
        sa.Column("reactions", sa.JSON(), nullable=False),
        sa.Column("identified_date", sa.Date(), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_allergies_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_allergies"),
    )
    op.create_index(
        "ix_clinical_allergy_patient_date",
        "clinical_allergies",
        ["tenant_id", "identity_domain", "master_patient_id", "identified_date"],
    )
    op.create_index(
        "ix_clinical_allergy_code",
        "clinical_allergies",
        ["allergen_system", "allergen_code"],
    )

    op.create_table(
        "clinical_medication_orders",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("medication_system", sa.String(256), nullable=True),
        sa.Column("medication_code", sa.String(128), nullable=True),
        sa.Column("medication_display", sa.String(512), nullable=True),
        sa.Column("status", sa.String(64), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_med_orders_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_medication_orders"),
    )
    op.create_index(
        "ix_clinical_med_order_patient",
        "clinical_medication_orders",
        ["tenant_id", "identity_domain", "master_patient_id"],
    )
    op.create_index(
        "ix_clinical_med_order_code",
        "clinical_medication_orders",
        ["medication_system", "medication_code"],
    )

    op.create_table(
        "clinical_medication_administrations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("medication_system", sa.String(256), nullable=True),
        sa.Column("medication_code", sa.String(128), nullable=True),
        sa.Column("medication_display", sa.String(512), nullable=True),
        sa.Column("status", sa.String(64), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_med_admins_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_medication_administrations"),
    )
    op.create_index(
        "ix_clinical_med_admin_patient_time",
        "clinical_medication_administrations",
        ["tenant_id", "identity_domain", "master_patient_id", "start_at"],
    )
    op.create_index(
        "ix_clinical_med_admin_code",
        "clinical_medication_administrations",
        ["medication_system", "medication_code"],
    )

    op.create_table(
        "clinical_coverages",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("payer_name", sa.String(512), nullable=True),
        sa.Column("group_number", sa.String(256), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_coverages_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_coverages"),
    )
    op.create_index(
        "ix_clinical_coverage_patient_dates",
        "clinical_coverages",
        ["tenant_id", "identity_domain", "master_patient_id", "effective_date"],
    )

    op.create_table(
        "clinical_provenance",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", UUID, nullable=False),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("source_message_id", sa.String(256), nullable=False),
        sa.Column("source_event_code", sa.String(64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_provenance_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_provenance"),
    )
    op.create_index(
        "ix_clinical_provenance_resource",
        "clinical_provenance",
        ["resource_type", "resource_id"],
    )
    op.create_index(
        "ix_clinical_provenance_source",
        "clinical_provenance",
        ["tenant_id", "identity_domain", "source_system", "source_message_id"],
    )

    op.create_table(
        "clinical_timeline_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("clinical_message_id", UUID, nullable=False),
        *_scope_columns(),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("resource_id", UUID, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("display", sa.String(512), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_message_id"],
            ["clinical_messages.id"],
            name="fk_clinical_timeline_message_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_timeline_events"),
    )
    op.create_index(
        "ix_clinical_timeline_patient_time",
        "clinical_timeline_events",
        ["tenant_id", "identity_domain", "master_patient_id", "occurred_at", "id"],
    )


def downgrade() -> None:
    op.drop_table("clinical_timeline_events")
    op.drop_table("clinical_provenance")
    op.drop_table("clinical_coverages")
    op.drop_table("clinical_medication_administrations")
    op.drop_table("clinical_medication_orders")
    op.drop_table("clinical_allergies")
    op.drop_table("clinical_observations")
    op.drop_table("clinical_diagnoses")
    op.drop_table("clinical_encounters")
    op.drop_table("clinical_messages")
