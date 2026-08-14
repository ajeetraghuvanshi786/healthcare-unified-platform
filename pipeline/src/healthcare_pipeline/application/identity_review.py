from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from healthcare_pipeline.identity.master.models import MasterPatientLink, ReviewCase
from healthcare_pipeline.identity.master.repository import MasterIdentityRepository
from healthcare_pipeline.identity.master.service import MasterPatientIdentityService
from healthcare_pipeline.identity.models import IdentityScope
from healthcare_pipeline.identity.store import IdentityCandidateStore


@dataclass(slots=True)
class IdentityReviewApplicationService:
    """Durable review decisions built from persisted encrypted source identity snapshots."""

    candidate_store: IdentityCandidateStore
    master_repository: MasterIdentityRepository

    def approve(
        self,
        review_case_id: UUID,
        *,
        candidate_record_id: str,
        scope: IdentityScope,
        actor_id: str,
    ) -> MasterPatientLink:
        review = self._review(review_case_id, scope)
        source = self.candidate_store.get(review.source_record_id)
        candidate = self.candidate_store.get(candidate_record_id)
        if source is None or candidate is None:
            raise ValueError("review source or candidate record is unavailable")
        if source.scope != scope or candidate.scope != scope:
            raise ValueError("review record scope mismatch")
        return MasterPatientIdentityService(self.master_repository).approve_review_link(
            review_case_id,
            source=source,
            candidate_record=candidate,
            actor_id=actor_id,
        )

    def reject(
        self,
        review_case_id: UUID,
        *,
        scope: IdentityScope,
        actor_id: str,
    ) -> ReviewCase:
        review = self._review(review_case_id, scope)
        source = self.candidate_store.get(review.source_record_id)
        if source is None:
            raise ValueError("review source record is unavailable")
        if source.scope != scope:
            raise ValueError("review record scope mismatch")
        return MasterPatientIdentityService(self.master_repository).reject_review(
            review_case_id,
            source=source,
            actor_id=actor_id,
        )

    def _review(self, review_case_id: UUID, scope: IdentityScope) -> ReviewCase:
        review = self.master_repository.get_review_case(review_case_id)
        if review is None or review.scope != scope:
            raise ValueError("review case does not exist")
        return review
