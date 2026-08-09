from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from healthcare_pipeline.canonical.demographics.patient import Patient


class IdentityResolutionStatus(StrEnum):
    NO_MATCH = "no_match"
    DETERMINISTIC_MATCH = "deterministic_match"
    POSSIBLE_MATCH = "possible_match"
    AMBIGUOUS = "ambiguous"
    CONFLICT = "conflict"


class MatchEvidenceType(StrEnum):
    SCOPED_IDENTIFIER_EXACT = "scoped_identifier_exact"
    NAME_EXACT = "name_exact"
    BIRTH_DATE_EXACT = "birth_date_exact"
    BIRTH_DATE_CONFLICT = "birth_date_conflict"
    PHONE_EXACT = "phone_exact"
    EMAIL_EXACT = "email_exact"
    POSTAL_CODE_EXACT = "postal_code_exact"


@dataclass(frozen=True, slots=True)
class IdentityScope:
    """Hard matching boundary preventing cross-tenant/cross-domain identity resolution."""

    tenant_id: str
    identity_domain: str

    def __post_init__(self) -> None:
        for field_name in ("tenant_id", "identity_domain"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            normalized = value.strip()
            if not normalized:
                raise ValueError(f"{field_name} must not be blank")
            object.__setattr__(self, field_name, normalized)


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    """Source patient record participating in identity resolution."""

    record_id: str
    source_system: str
    scope: IdentityScope
    patient: Patient

    def __post_init__(self) -> None:
        for field_name in ("record_id", "source_system"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            normalized = value.strip()
            if not normalized:
                raise ValueError(f"{field_name} must not be blank")
            object.__setattr__(self, field_name, normalized)
        if not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be an IdentityScope")
        if not isinstance(self.patient, Patient):
            raise TypeError("patient must be a canonical Patient")


@dataclass(frozen=True, slots=True)
class MatchEvidence:
    """PHI-safe evidence descriptor; carries no patient values."""

    evidence_type: MatchEvidenceType
    source_path: str
    candidate_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_type, MatchEvidenceType):
            raise TypeError("evidence_type must be a MatchEvidenceType")
        for field_name in ("source_path", "candidate_path"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-blank string")
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True, slots=True)
class IdentityCandidateMatch:
    candidate_record_id: str
    status: IdentityResolutionStatus
    evidence: tuple[MatchEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_record_id, str) or not self.candidate_record_id.strip():
            raise ValueError("candidate_record_id must be a non-blank string")
        object.__setattr__(self, "candidate_record_id", self.candidate_record_id.strip())
        if not isinstance(self.status, IdentityResolutionStatus):
            raise TypeError("status must be an IdentityResolutionStatus")
        evidence = tuple(self.evidence)
        if not all(isinstance(item, MatchEvidence) for item in evidence):
            raise TypeError("evidence contains an invalid value")
        object.__setattr__(self, "evidence", evidence)


@dataclass(frozen=True, slots=True)
class IdentityResolutionResult:
    status: IdentityResolutionStatus
    matches: tuple[IdentityCandidateMatch, ...] = ()
    selected_record_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdentityResolutionStatus):
            raise TypeError("status must be an IdentityResolutionStatus")
        matches = tuple(self.matches)
        if not all(isinstance(item, IdentityCandidateMatch) for item in matches):
            raise TypeError("matches contains an invalid value")
        object.__setattr__(self, "matches", matches)
        if self.selected_record_id is not None:
            normalized = self.selected_record_id.strip()
            if not normalized:
                raise ValueError("selected_record_id must not be blank")
            object.__setattr__(self, "selected_record_id", normalized)
        if self.status is IdentityResolutionStatus.DETERMINISTIC_MATCH:
            if self.selected_record_id is None:
                raise ValueError("deterministic match requires selected_record_id")
        elif self.selected_record_id is not None:
            raise ValueError("only deterministic match may select a record")

    @property
    def requires_manual_review(self) -> bool:
        return self.status in {
            IdentityResolutionStatus.POSSIBLE_MATCH,
            IdentityResolutionStatus.AMBIGUOUS,
            IdentityResolutionStatus.CONFLICT,
        }
