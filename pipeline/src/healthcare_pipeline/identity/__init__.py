from healthcare_pipeline.identity.keying import HmacIdentityKeyEncoder, IdentityKeyEncoder
from healthcare_pipeline.identity.matcher import DeterministicPatientMatcher
from healthcare_pipeline.identity.models import (
    IdentityCandidateMatch,
    IdentityRecord,
    IdentityResolutionResult,
    IdentityResolutionStatus,
    IdentityScope,
    MatchEvidence,
    MatchEvidenceType,
)
from healthcare_pipeline.identity.normalization import (
    NormalizedPatientIdentity,
    PatientIdentityNormalizer,
)
from healthcare_pipeline.identity.resolver import PatientIdentityResolver
from healthcare_pipeline.identity.service import PatientIdentityService
from healthcare_pipeline.identity.store import (
    IdentityCandidateStore,
    InMemoryIdentityCandidateStore,
)

__all__ = [
    "DeterministicPatientMatcher",
    "HmacIdentityKeyEncoder",
    "IdentityCandidateMatch",
    "IdentityCandidateStore",
    "IdentityKeyEncoder",
    "IdentityRecord",
    "IdentityResolutionResult",
    "IdentityResolutionStatus",
    "IdentityScope",
    "InMemoryIdentityCandidateStore",
    "MatchEvidence",
    "MatchEvidenceType",
    "NormalizedPatientIdentity",
    "PatientIdentityNormalizer",
    "PatientIdentityResolver",
    "PatientIdentityService",
]

from healthcare_pipeline.identity.master import (
    IdentityDecisionAction,
    IdentityDecisionEvent,
    IdentityDecisionReason,
    InMemoryMasterIdentityRepository,
    MasterIdentityRepository,
    MasterPatient,
    MasterPatientIdentityService,
    MasterPatientLink,
    MasterPatientLinkStatus,
    ReviewCase,
    ReviewCaseStatus,
)

__all__ += [
    "IdentityDecisionAction",
    "IdentityDecisionEvent",
    "IdentityDecisionReason",
    "InMemoryMasterIdentityRepository",
    "MasterIdentityRepository",
    "MasterPatient",
    "MasterPatientIdentityService",
    "MasterPatientLink",
    "MasterPatientLinkStatus",
    "ReviewCase",
    "ReviewCaseStatus",
]
