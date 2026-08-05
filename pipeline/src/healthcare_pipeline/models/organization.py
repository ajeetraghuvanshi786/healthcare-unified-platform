from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
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
from healthcare_pipeline.models.enums import OrganizationType

if TYPE_CHECKING:
    from healthcare_pipeline.models.location import Location
    from healthcare_pipeline.models.organization_identifier import (
        OrganizationIdentifier,
    )
    from healthcare_pipeline.models.tenant import Tenant


class Organization(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """Healthcare, payer, pharmacy, laboratory, or administrative organization."""

    __tablename__ = "organization"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 2",
            name="name_min_length",
        ),
        UniqueConstraint(
            "tenant_id",
            "code",
            name="tenant_code",
        ),
        Index(
            "ix_organization_tenant_parent",
            "tenant_id",
            "parent_organization_id",
        ),
        Index(
            "ix_organization_tenant_type_active",
            "tenant_id",
            "organization_type",
            "is_active",
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

    parent_organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organization.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organization_type: Mapped[OrganizationType] = mapped_column(
        Enum(
            OrganizationType,
            name="organization_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    tenant: Mapped[Tenant] = relationship(
        back_populates="organizations",
    )

    parent_organization: Mapped[Organization | None] = relationship(
        remote_side="Organization.id",
        back_populates="child_organizations",
    )

    child_organizations: Mapped[list[Organization]] = relationship(
        back_populates="parent_organization",
    )

    identifiers: Mapped[list[OrganizationIdentifier]] = relationship(
        back_populates="organization",
        cascade="save-update, merge",
    )

    locations: Mapped[list[Location]] = relationship(
        back_populates="managing_organization",
        cascade="save-update, merge",
    )