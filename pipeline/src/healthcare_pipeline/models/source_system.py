from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
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
    VersionMixin,
)
from healthcare_pipeline.models.enums import DataStandard, SourceSystemType

if TYPE_CHECKING:
    from healthcare_pipeline.models.organization import Organization
    from healthcare_pipeline.models.tenant import Tenant


class SourceSystem(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """Registered technical system that supplies data to the platform."""

    __tablename__ = "source_system"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 2",
            name="name_min_length",
        ),
        CheckConstraint(
            "char_length(trim(code)) >= 2",
            name="code_min_length",
        ),
        UniqueConstraint(
            "tenant_id",
            "code",
            name="tenant_code",
        ),
        Index(
            "ix_source_system_tenant_organization",
            "tenant_id",
            "organization_id",
        ),
        Index(
            "ix_source_system_tenant_active",
            "tenant_id",
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

    organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organization.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_system_type: Mapped[SourceSystemType] = mapped_column(
        Enum(
            SourceSystemType,
            name="source_system_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    primary_standard: Mapped[DataStandard] = mapped_column(
        Enum(
            DataStandard,
            name="data_standard",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    vendor_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    product_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    product_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    environment: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="production",
        server_default="production",
    )

    endpoint_uri: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    tenant: Mapped[Tenant] = relationship(
        back_populates="source_systems",
    )

    organization: Mapped[Organization | None] = relationship()