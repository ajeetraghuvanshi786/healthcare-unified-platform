"""add durable master identity, encrypted candidate index, review and audit tables

Revision ID: 20260811_01
Revises: None
Create Date: 2026-08-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260811_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_master_patients"),
    )

    op.create_index(
        "ix_master_patients_scope",
        "master_patients",
        ["tenant_id", "identity_domain", "id"],
    )

    op.create_table(
        "identity_review_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("source_record_id", sa.String(128), nullable=False),
        sa.Column("candidate_record_ids", sa.JSON(), nullable=False),
        sa.Column("resolution_status", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_identity_review_cases"),
    )

    op.create_index(
        "ix_identity_reviews_scope_status",
        "identity_review_cases",
        ["tenant_id", "identity_domain", "status"],
    )

    op.create_table(
        "master_patient_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "master_patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("source_record_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'unlinked')",
            name="ck_master_patient_links_master_link_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["master_patient_id"],
            ["master_patients.id"],
            name="fk_master_patient_links_master_patient_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_master_patient_links",
        ),
    )

    op.create_index(
        "ix_master_links_master_active",
        "master_patient_links",
        ["master_patient_id", "status"],
    )

    op.create_index(
        "uq_master_links_active_source",
        "master_patient_links",
        [
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_record_id",
        ],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "identity_decision_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(48), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("source_record_id", sa.String(128), nullable=False),
        sa.Column(
            "master_patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "review_case_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["master_patient_id"],
            ["master_patients.id"],
            name="fk_identity_decision_events_master_patient_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["review_case_id"],
            ["identity_review_cases.id"],
            name="fk_identity_decision_events_review_case_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_identity_decision_events",
        ),
    )

    op.create_index(
        "ix_identity_events_master_time",
        "identity_decision_events",
        ["master_patient_id", "occurred_at"],
    )

    op.create_index(
        "ix_identity_events_review_time",
        "identity_decision_events",
        ["review_case_id", "occurred_at"],
    )

    op.create_index(
        "ix_identity_events_scope_time",
        "identity_decision_events",
        ["tenant_id", "identity_domain", "occurred_at"],
    )

    op.create_table(
        "identity_source_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("source_record_id", sa.String(128), nullable=False),
        sa.Column("encryption_key_id", sa.String(64), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_identity_source_records",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "identity_domain",
            "source_system",
            "source_record_id",
            name="uq_identity_source_record_scope",
        ),
    )

    op.create_index(
        "ix_identity_source_record_token",
        "identity_source_records",
        ["source_record_id"],
    )

    op.create_table(
        "identity_candidate_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "source_record_db_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("identity_domain", sa.String(128), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_record_db_id"],
            ["identity_source_records.id"],
            name="fk_identity_candidate_keys_source_record_db_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_identity_candidate_keys",
        ),
        sa.UniqueConstraint(
            "source_record_db_id",
            "key_hash",
            name="uq_identity_candidate_record_key",
        ),
    )

    op.create_index(
        "ix_identity_candidate_lookup",
        "identity_candidate_keys",
        ["tenant_id", "identity_domain", "key_hash"],
    )


def downgrade() -> None:
    op.drop_table("identity_candidate_keys")
    op.drop_table("identity_source_records")
    op.drop_table("identity_decision_events")
    op.drop_table("master_patient_links")
    op.drop_table("identity_review_cases")
    op.drop_table("master_patients")