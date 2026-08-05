from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
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
from healthcare_pipeline.models.enums import (
    LocationMode,
    LocationStatus,
    LocationType,
)

if TYPE_CHECKING:
    from healthcare_pipeline.models.organization import Organization


class Location(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    VersionMixin,
    Base,
):
    """Physical or virtual place where care or operational activity occurs."""

    __tablename__ = "location"

    __table_args__ = (
        CheckConstraint(
            "char_length(trim(name)) >= 1",
            name="name_not_blank",
        ),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="longitude_range",
        ),
        UniqueConstraint(
            "tenant_id",
            "code",
            name="tenant_code",
        ),
        Index(
            "ix_location_tenant_organization",
            "tenant_id",
            "managing_organization_id",
        ),
        Index(
            "ix_location_parent",
            "parent_location_id",
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

    managing_organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "organization.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    parent_location_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "location.id",
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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[LocationStatus] = mapped_column(
        Enum(
            LocationStatus,
            name="location_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=LocationStatus.ACTIVE,
        server_default=LocationStatus.ACTIVE.value,
    )

    mode: Mapped[LocationMode] = mapped_column(
        Enum(
            LocationMode,
            name="location_mode",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
        default=LocationMode.INSTANCE,
        server_default=LocationMode.INSTANCE.value,
    )

    location_type: Mapped[LocationType] = mapped_column(
        Enum(
            LocationType,
            name="location_type",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    address_line_1: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address_line_2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
        server_default="US",
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    managing_organization: Mapped[Organization | None] = relationship(
        back_populates="locations",
    )

    parent_location: Mapped[Location | None] = relationship(
        remote_side="Location.id",
        back_populates="child_locations",
    )

    child_locations: Mapped[list[Location]] = relationship(
        back_populates="parent_location",
    )