from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.identity.matcher import DeterministicPatientMatcher
from healthcare_pipeline.identity.models import (
    IdentityCandidateMatch,
    IdentityRecord,
    IdentityResolutionResult,
    IdentityResolutionStatus,
)
from healthcare_pipeline.identity.store import IdentityCandidateStore


@dataclass(frozen=True, slots=True)
class PatientIdentityResolver:
    """Candidate generation + deterministic evaluation; never performs merge/write actions."""

    store: IdentityCandidateStore
    matcher: DeterministicPatientMatcher = DeterministicPatientMatcher()
    max_candidates: int = 100

    def __post_init__(self) -> None:
        if not isinstance(self.max_candidates, int) or self.max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")

    def resolve(self, source: IdentityRecord) -> IdentityResolutionResult:
        candidate_ids = self.store.candidate_ids(source)
        if len(candidate_ids) > self.max_candidates:
            return IdentityResolutionResult(IdentityResolutionStatus.AMBIGUOUS)

        matches: list[IdentityCandidateMatch] = []
        for record_id in candidate_ids:
            candidate = self.store.get(record_id)
            if candidate is None or candidate.scope != source.scope:
                continue
            match = self.matcher.compare(source, candidate)
            if match.status is not IdentityResolutionStatus.NO_MATCH:
                matches.append(match)

        conflicts = [m for m in matches if m.status is IdentityResolutionStatus.CONFLICT]
        deterministic = [
            m for m in matches if m.status is IdentityResolutionStatus.DETERMINISTIC_MATCH
        ]
        possible = [m for m in matches if m.status is IdentityResolutionStatus.POSSIBLE_MATCH]

        if conflicts:
            return IdentityResolutionResult(
                IdentityResolutionStatus.CONFLICT,
                tuple(sorted(conflicts, key=lambda item: item.candidate_record_id)),
            )
        if len(deterministic) == 1:
            selected = deterministic[0]
            return IdentityResolutionResult(
                IdentityResolutionStatus.DETERMINISTIC_MATCH,
                (selected,),
                selected.candidate_record_id,
            )
        if len(deterministic) > 1:
            return IdentityResolutionResult(
                IdentityResolutionStatus.AMBIGUOUS,
                tuple(sorted(deterministic, key=lambda item: item.candidate_record_id)),
            )
        if possible:
            return IdentityResolutionResult(
                IdentityResolutionStatus.POSSIBLE_MATCH,
                tuple(sorted(possible, key=lambda item: item.candidate_record_id)),
            )
        return IdentityResolutionResult(IdentityResolutionStatus.NO_MATCH)
