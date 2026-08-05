from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from healthcare_pipeline.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from healthcare_pipeline.models.enums import TenantStatus

if TYPE_CHECKING:
    from healthcare_pipeline.models.assigning_authority import AssigningAuthority
    from healthcare_pipeline.models.organization import Organization
    from healthcare_pipeline.models.source_system import SourceSystem


class Tenant(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """Top-level customer and data-isolation boundary."""

    __tablename__ = "tenant"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 2",
            name="name_min_length",
        ),
        CheckConstraint(
            "char_length(trim(code)) >= 2",
            name="code_min_length",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[TenantStatus] = mapped_column(
        Enum(
            TenantStatus,
            name="tenant_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=TenantStatus.ACTIVE,
        server_default=TenantStatus.ACTIVE.value,
        index=True,
    )

    organizations: Mapped[list[Organization]] = relationship(
        back_populates="tenant",
        cascade="save-update, merge",
    )

    source_systems: Mapped[list[SourceSystem]] = relationship(
        back_populates="tenant",
        cascade="save-update, merge",
    )

    assigning_authorities: Mapped[list[AssigningAuthority]] = relationship(
        back_populates="tenant",
        cascade="save-update, merge",
    )