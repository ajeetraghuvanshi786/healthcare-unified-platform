"""Public SQLAlchemy model package and shared metadata registration point."""

from healthcare_pipeline.models.assigning_authority import AssigningAuthority
from healthcare_pipeline.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin
from healthcare_pipeline.models.clinical import (
    ClinicalAllergyRecord,
    ClinicalCoverageRecord,
    ClinicalDiagnosisRecord,
    ClinicalEncounterRecord,
    ClinicalMedicationAdministrationRecord,
    ClinicalMedicationOrderRecord,
    ClinicalMessageRecord,
    ClinicalObservationRecord,
    ClinicalProvenanceRecord,
    ClinicalTimelineEventRecord,
)
from healthcare_pipeline.models.dead_letter_record import DeadLetterRecord
from healthcare_pipeline.models.enums import (
    CheckpointStatus,
    CompressionType,
    DataStandard,
    DeadLetterStatus,
    ErrorRecoverability,
    IngestionBatchStatus,
    IngestionTransport,
    LocationMode,
    LocationStatus,
    LocationType,
    OrganizationIdentifierType,
    OrganizationType,
    PayloadEncoding,
    ProcessingJobStatus,
    ProcessingStage,
    RawRecordStatus,
    SourceSystemType,
    TenantStatus,
    TransformationStatus,
    ValidationCategory,
    ValidationOutcome,
    ValidationSeverity,
)
from healthcare_pipeline.models.identity_master import (
    IdentityCandidateKeyModel,
    IdentityDecisionEventModel,
    IdentityReviewCaseModel,
    IdentitySourceRecordModel,
    MasterPatientLinkModel,
    MasterPatientModel,
)
from healthcare_pipeline.models.ingestion_batch import IngestionBatch
from healthcare_pipeline.models.location import Location
from healthcare_pipeline.models.organization import Organization
from healthcare_pipeline.models.organization_identifier import OrganizationIdentifier
from healthcare_pipeline.models.processing_checkpoint import ProcessingCheckpoint
from healthcare_pipeline.models.processing_job import ProcessingJob
from healthcare_pipeline.models.raw_ingestion_record import RawIngestionRecord
from healthcare_pipeline.models.source_system import SourceSystem
from healthcare_pipeline.models.tenant import Tenant
from healthcare_pipeline.models.transformation_log import TransformationLog
from healthcare_pipeline.models.validation_result import ValidationResult

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "VersionMixin",
    "AssigningAuthority",
    "Location",
    "Organization",
    "OrganizationIdentifier",
    "SourceSystem",
    "Tenant",
    "IngestionBatch",
    "RawIngestionRecord",
    "ClinicalMessageRecord",
    "ClinicalEncounterRecord",
    "ClinicalDiagnosisRecord",
    "ClinicalObservationRecord",
    "ClinicalAllergyRecord",
    "ClinicalMedicationOrderRecord",
    "ClinicalMedicationAdministrationRecord",
    "ClinicalCoverageRecord",
    "ClinicalProvenanceRecord",
    "ClinicalTimelineEventRecord",
    "MasterPatientModel",
    "MasterPatientLinkModel",
    "IdentityReviewCaseModel",
    "IdentityDecisionEventModel",
    "IdentitySourceRecordModel",
    "IdentityCandidateKeyModel",
    "ProcessingJob",
    "ValidationResult",
    "TransformationLog",
    "DeadLetterRecord",
    "ProcessingCheckpoint",
    "LocationMode",
    "LocationStatus",
    "LocationType",
    "OrganizationIdentifierType",
    "OrganizationType",
    "SourceSystemType",
    "TenantStatus",
    "DataStandard",
    "CompressionType",
    "IngestionBatchStatus",
    "IngestionTransport",
    "PayloadEncoding",
    "RawRecordStatus",
    "ProcessingJobStatus",
    "ProcessingStage",
    "ValidationSeverity",
    "ValidationCategory",
    "ValidationOutcome",
    "TransformationStatus",
    "DeadLetterStatus",
    "ErrorRecoverability",
    "CheckpointStatus",
]
