from healthcare_pipeline import models
from healthcare_pipeline.models import (
    AssigningAuthority,
    Base,
    CheckpointStatus,
    CompressionType,
    DataStandard,
    DeadLetterRecord,
    DeadLetterStatus,
    ErrorRecoverability,
    IngestionBatch,
    IngestionBatchStatus,
    IngestionTransport,
    Location,
    LocationMode,
    LocationStatus,
    LocationType,
    Organization,
    OrganizationIdentifier,
    OrganizationIdentifierType,
    OrganizationType,
    PayloadEncoding,
    ProcessingCheckpoint,
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingStage,
    RawIngestionRecord,
    RawRecordStatus,
    SourceSystem,
    SourceSystemType,
    Tenant,
    TenantStatus,
    TimestampMixin,
    TransformationLog,
    TransformationStatus,
    UUIDPrimaryKeyMixin,
    ValidationCategory,
    ValidationOutcome,
    ValidationResult,
    ValidationSeverity,
    VersionMixin,
)


def test_foundation_models_are_exported() -> None:
    assert models.Base is Base
    assert models.UUIDPrimaryKeyMixin is UUIDPrimaryKeyMixin
    assert models.TimestampMixin is TimestampMixin
    assert models.VersionMixin is VersionMixin


def test_phase_2b_models_are_exported() -> None:
    assert models.Tenant is Tenant
    assert models.Organization is Organization
    assert models.OrganizationIdentifier is OrganizationIdentifier
    assert models.Location is Location
    assert models.SourceSystem is SourceSystem
    assert models.AssigningAuthority is AssigningAuthority


def test_phase_2c_models_are_exported() -> None:
    assert models.IngestionBatch is IngestionBatch
    assert models.RawIngestionRecord is RawIngestionRecord
    assert models.ProcessingJob is ProcessingJob
    assert models.ValidationResult is ValidationResult
    assert models.TransformationLog is TransformationLog
    assert models.DeadLetterRecord is DeadLetterRecord
    assert models.ProcessingCheckpoint is ProcessingCheckpoint


def test_phase_2b_enums_are_exported() -> None:
    assert models.TenantStatus is TenantStatus
    assert models.OrganizationType is OrganizationType
    assert models.OrganizationIdentifierType is OrganizationIdentifierType
    assert models.LocationStatus is LocationStatus
    assert models.LocationMode is LocationMode
    assert models.LocationType is LocationType
    assert models.SourceSystemType is SourceSystemType
    assert models.DataStandard is DataStandard


def test_phase_2c_enums_are_exported() -> None:
    expected = {
        "IngestionBatchStatus": IngestionBatchStatus,
        "IngestionTransport": IngestionTransport,
        "RawRecordStatus": RawRecordStatus,
        "PayloadEncoding": PayloadEncoding,
        "CompressionType": CompressionType,
        "ProcessingJobStatus": ProcessingJobStatus,
        "ProcessingStage": ProcessingStage,
        "ValidationSeverity": ValidationSeverity,
        "ValidationCategory": ValidationCategory,
        "ValidationOutcome": ValidationOutcome,
        "TransformationStatus": TransformationStatus,
        "DeadLetterStatus": DeadLetterStatus,
        "ErrorRecoverability": ErrorRecoverability,
        "CheckpointStatus": CheckpointStatus,
    }
    for name, value in expected.items():
        assert getattr(models, name) is value


def test_all_exports_reference_existing_attributes() -> None:
    for exported_name in models.__all__:
        assert hasattr(models, exported_name), (
            f"{exported_name!r} is included in models.__all__ "
            "but is not available on the models package"
        )


def test_models_are_registered_in_base_metadata() -> None:
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "tenant",
        "organization",
        "organization_identifier",
        "location",
        "source_system",
        "assigning_authority",
        "ingestion_batch",
        "raw_ingestion_record",
        "processing_job",
        "validation_result",
        "transformation_log",
        "dead_letter_record",
        "processing_checkpoint",
    }
    assert expected_tables.issubset(table_names)
