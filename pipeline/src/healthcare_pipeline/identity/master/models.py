from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from healthcare_pipeline.identity.models import IdentityResolutionStatus, IdentityScope


class MasterPatientLinkStatus(StrEnum):
    ACTIVE = "active"
    UNLINKED = "unlinked"


class ReviewCaseStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class IdentityDecisionAction(StrEnum):
    MASTER_CREATED = "master_created"
    RECORD_LINKED = "record_linked"
    RECORD_UNLINKED = "record_unlinked"
    REVIEW_OPENED = "review_opened"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    REVIEW_CANCELLED = "review_cancelled"


class IdentityDecisionReason(StrEnum):
    DETERMINISTIC_IDENTIFIER = "deterministic_identifier"
    MANUAL_REVIEW_APPROVED = "manual_review_approved"
    MANUAL_REVIEW_REJECTED = "manual_review_rejected"
    DATA_CORRECTION = "data_correction"
    DUPLICATE_REGISTRATION = "duplicate_registration"
    WRONG_PATIENT_LINK = "wrong_patient_link"
    ADMINISTRATIVE_CORRECTION = "administrative_correction"


def _require_non_blank(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _aware_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class MasterPatient:
    """Stable enterprise identity container; it does not overwrite source patient records."""

    scope: IdentityScope
    master_patient_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_aware_now)

    def __post_init__(self) -> None:
        if not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be an IdentityScope")
        if not isinstance(self.master_patient_id, UUID):
            raise TypeError("master_patient_id must be a UUID")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class MasterPatientLink:
    """Link between one immutable source identity record and one master patient."""

    master_patient_id: UUID
    source_record_id: str
    source_system: str
    scope: IdentityScope
    status: MasterPatientLinkStatus = MasterPatientLinkStatus.ACTIVE
    linked_at: datetime = _aware_now()
    unlinked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.master_patient_id, UUID):
            raise TypeError("master_patient_id must be a UUID")
        object.__setattr__(
            self,
            "source_record_id",
            _require_non_blank(self.source_record_id, "source_record_id"),
        )
        object.__setattr__(
            self,
            "source_system",
            _require_non_blank(self.source_system, "source_system"),
        )
        if not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be an IdentityScope")
        if not isinstance(self.status, MasterPatientLinkStatus):
            raise TypeError("status must be a MasterPatientLinkStatus")
        for field_name in ("linked_at", "unlinked_at"):
            value = getattr(self, field_name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.status is MasterPatientLinkStatus.ACTIVE and self.unlinked_at is not None:
            raise ValueError("active link must not have unlinked_at")
        if self.status is MasterPatientLinkStatus.UNLINKED and self.unlinked_at is None:
            raise ValueError("unlinked link requires unlinked_at")
        if self.unlinked_at is not None and self.unlinked_at < self.linked_at:
            raise ValueError("unlinked_at must not precede linked_at")

    def unlink(self, *, at: datetime | None = None) -> MasterPatientLink:
        if self.status is MasterPatientLinkStatus.UNLINKED:
            return self
        unlink_time = at or _aware_now()
        return MasterPatientLink(
            master_patient_id=self.master_patient_id,
            source_record_id=self.source_record_id,
            source_system=self.source_system,
            scope=self.scope,
            status=MasterPatientLinkStatus.UNLINKED,
            linked_at=self.linked_at,
            unlinked_at=unlink_time,
        )


@dataclass(frozen=True, slots=True)
class ReviewCase:
    """Human-review case created for uncertain/ambiguous/conflicting identity decisions."""

    source_record_id: str
    candidate_record_ids: tuple[str, ...]
    resolution_status: IdentityResolutionStatus
    scope: IdentityScope
    review_case_id: UUID = field(default_factory=uuid4)
    status: ReviewCaseStatus = ReviewCaseStatus.OPEN
    opened_at: datetime = field(default_factory=_aware_now)
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_record_id",
            _require_non_blank(self.source_record_id, "source_record_id"),
        )
        candidate_ids = tuple(
            _require_non_blank(item, "candidate_record_id")
            for item in self.candidate_record_ids
        )
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("candidate_record_ids must not contain duplicates")
        object.__setattr__(self, "candidate_record_ids", candidate_ids)
        if not isinstance(self.resolution_status, IdentityResolutionStatus):
            raise TypeError("resolution_status must be an IdentityResolutionStatus")
        if self.resolution_status not in {
            IdentityResolutionStatus.POSSIBLE_MATCH,
            IdentityResolutionStatus.AMBIGUOUS,
            IdentityResolutionStatus.CONFLICT,
        }:
            raise ValueError("review case requires a reviewable resolution status")
        if not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be an IdentityScope")
        if not isinstance(self.review_case_id, UUID):
            raise TypeError("review_case_id must be a UUID")
        if not isinstance(self.status, ReviewCaseStatus):
            raise TypeError("status must be a ReviewCaseStatus")
        for field_name in ("opened_at", "closed_at"):
            value = getattr(self, field_name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.status is ReviewCaseStatus.OPEN and self.closed_at is not None:
            raise ValueError("open review case must not have closed_at")
        if self.status is not ReviewCaseStatus.OPEN and self.closed_at is None:
            raise ValueError("closed review case requires closed_at")

    def close(self, status: ReviewCaseStatus, *, at: datetime | None = None) -> ReviewCase:
        if status is ReviewCaseStatus.OPEN:
            raise ValueError("close status must not be OPEN")
        if self.status is not ReviewCaseStatus.OPEN:
            raise ValueError("review case is already closed")
        return ReviewCase(
            source_record_id=self.source_record_id,
            candidate_record_ids=self.candidate_record_ids,
            resolution_status=self.resolution_status,
            scope=self.scope,
            review_case_id=self.review_case_id,
            status=status,
            opened_at=self.opened_at,
            closed_at=at or _aware_now(),
        )


@dataclass(frozen=True, slots=True)
class IdentityDecisionEvent:
    """Append-only PHI-safe audit event for identity lifecycle decisions."""

    action: IdentityDecisionAction
    reason: IdentityDecisionReason
    actor_id: str
    scope: IdentityScope
    source_record_id: str
    event_id: UUID = field(default_factory=uuid4)
    master_patient_id: UUID | None = None
    review_case_id: UUID | None = None
    occurred_at: datetime = field(default_factory=_aware_now)

    def __post_init__(self) -> None:
        if not isinstance(self.action, IdentityDecisionAction):
            raise TypeError("action must be an IdentityDecisionAction")
        if not isinstance(self.reason, IdentityDecisionReason):
            raise TypeError("reason must be an IdentityDecisionReason")
        object.__setattr__(self, "actor_id", _require_non_blank(self.actor_id, "actor_id"))
        object.__setattr__(
            self,
            "source_record_id",
            _require_non_blank(self.source_record_id, "source_record_id"),
        )
        if not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be an IdentityScope")
        if not isinstance(self.event_id, UUID):
            raise TypeError("event_id must be a UUID")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
