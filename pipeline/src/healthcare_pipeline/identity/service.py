from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.identity.models import IdentityRecord, IdentityResolutionResult
from healthcare_pipeline.identity.resolver import PatientIdentityResolver
from healthcare_pipeline.identity.store import IdentityCandidateStore


@dataclass(frozen=True, slots=True)
class PatientIdentityService:
    """Application-facing identity service. Resolution and indexing remain explicit operations."""

    store: IdentityCandidateStore
    resolver: PatientIdentityResolver

    @classmethod
    def create(
        cls,
        store: IdentityCandidateStore,
        *,
        max_candidates: int = 100,
    ) -> PatientIdentityService:
        resolver = PatientIdentityResolver(store, max_candidates=max_candidates)
        return cls(store=store, resolver=resolver)

    def resolve(self, record: IdentityRecord) -> IdentityResolutionResult:
        return self.resolver.resolve(record)

    def index(self, record: IdentityRecord) -> None:
        self.store.upsert(record)

    def resolve_then_index(self, record: IdentityRecord) -> IdentityResolutionResult:
        """Resolve against prior records, then index source. This method never merges patients."""
        result = self.resolve(record)
        self.index(record)
        return result
