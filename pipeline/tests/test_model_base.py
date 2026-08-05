from healthcare_pipeline.models.base import (
    NAMING_CONVENTION,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)


def test_base_uses_enterprise_constraint_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_primary_key_mixin_defines_id_column() -> None:
    assert "id" in UUIDPrimaryKeyMixin.__annotations__


def test_timestamp_mixin_defines_audit_timestamps() -> None:
    assert "created_at" in TimestampMixin.__annotations__
    assert "updated_at" in TimestampMixin.__annotations__


def test_version_mixin_defines_version_column() -> None:
    assert "version" in VersionMixin.__annotations__