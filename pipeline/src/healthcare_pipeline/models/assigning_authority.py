from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
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

if TYPE_CHECKING:
    from healthcare_pipeline.models.organization import Organization
    from healthcare_pipeline.models.source_system import SourceSystem
    from healthcare_pipeline.models.tenant import Tenant


class AssigningAuthority(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """Namespace or authority responsible for issuing external identifiers."""

    __tablename__ = "assigning_authority"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 2",
            name="name_min_length",
        ),
        CheckConstraint(
            "char_length(trim(namespace_uri)) >= 3",
            name="namespace_uri_min_length",
        ),
        UniqueConstraint(
            "tenant_id",
            "namespace_uri",
            name="tenant_namespace_uri",
        ),
        Index(
            "ix_assigning_authority_tenant_organization",
            "tenant_id",
            "organization_id",
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

    source_system_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "source_system.id",
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

    namespace_uri: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    universal_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    universal_id_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        server_default="true",
    )

    tenant: Mapped[Tenant] = relationship(
        back_populates="assigning_authorities",
    )

    organization: Mapped[Organization | None] = relationship()

    source_system: Mapped[SourceSystem | None] = relationship()