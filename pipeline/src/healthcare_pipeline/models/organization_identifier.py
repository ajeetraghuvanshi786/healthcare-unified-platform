from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from healthcare_pipeline.models.enums import OrganizationIdentifierType

if TYPE_CHECKING:
    from healthcare_pipeline.models.organization import Organization


class OrganizationIdentifier(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """Externally meaningful identifier issued to a healthcare organization."""

    __tablename__ = "organization_identifier"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(system)) >= 3",
            name="system_min_length",
        ),
        CheckConstraint(
            "char_length(trim(value)) >= 1",
            name="value_not_blank",
        ),
        CheckConstraint(
            "period_end IS NULL OR period_start IS NULL "
            "OR period_end >= period_start",
            name="valid_period",
        ),
        UniqueConstraint(
            "organization_id",
            "system",
            "value",
            name="organization_system_value",
        ),
        Index(
            "ix_organization_identifier_lookup",
            "system",
            "value",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organization.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    identifier_type: Mapped[OrganizationIdentifierType] = mapped_column(
        Enum(
            OrganizationIdentifierType,
            name="organization_identifier_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    system: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    period_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
    )

    organization: Mapped[Organization] = relationship(
        back_populates="identifiers",
    )