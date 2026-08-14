from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from healthcare_pipeline.identity.master.models import (
    IdentityDecisionAction,
    IdentityDecisionEvent,
    IdentityDecisionReason,
    MasterPatient,
    MasterPatientLink,
    ReviewCase,
    ReviewCaseStatus,
)
from healthcare_pipeline.identity.master.repository import MasterIdentityRepository
from healthcare_pipeline.identity.models import (
    IdentityRecord,
    IdentityResolutionResult,
    IdentityScope,
)


@dataclass(frozen=True, slots=True)
class MasterPatientIdentityService:
    """Controlled identity-link lifecycle. Never merges or deletes source patient records."""

    repository: MasterIdentityRepository

    def create_master_and_link(
        self,
        record: IdentityRecord,
        *,
        actor_id: str,
        reason: IdentityDecisionReason = IdentityDecisionReason.DETERMINISTIC_IDENTIFIER,
    ) -> MasterPatient:
        existing = self.repository.active_link_for_record(
            scope=record.scope,
            source_record_id=record.record_id,
            source_system=record.source_system,
        )
        if existing is not None:
            master = self.repository.get_master(existing.master_patient_id)
            if master is None:
                raise RuntimeError("identity repository integrity violation")
            return master

        master = MasterPatient(scope=record.scope)
        self.repository.create_master(master)
        self._link_record(
            master=master,
            record=record,
            actor_id=actor_id,
            reason=reason,
            action=IdentityDecisionAction.MASTER_CREATED,
        )
        return master

    def link_to_master(
        self,
        master_patient_id: UUID,
        record: IdentityRecord,
        *,
        actor_id: str,
        reason: IdentityDecisionReason,
    ) -> MasterPatientLink:
        master = self.repository.get_master(master_patient_id)
        if master is None:
            raise ValueError("master patient does not exist")
        if master.scope != record.scope:
            raise ValueError("cross-scope identity links are prohibited")

        current = self.repository.active_link_for_record(
            scope=record.scope,
            source_record_id=record.record_id,
            source_system=record.source_system,
        )
        if current is not None:
            if current.master_patient_id == master_patient_id:
                return current
            raise ValueError("source record is already linked to another master patient")

        return self._link_record(
            master=master,
            record=record,
            actor_id=actor_id,
            reason=reason,
            action=IdentityDecisionAction.RECORD_LINKED,
        )

    def unlink_record(
        self,
        *,
        scope: IdentityScope,
        source_record_id: str,
        source_system: str | None = None,
        actor_id: str,
        reason: IdentityDecisionReason,
    ) -> MasterPatientLink:
        current = self.repository.active_link_for_record(
            scope=scope,
            source_record_id=source_record_id,
            source_system=source_system,
        )
        if current is None:
            raise ValueError("source record has no active master link")
        unlinked = current.unlink(at=datetime.now(UTC))
        self.repository.save_link(unlinked)
        self.repository.append_event(
            IdentityDecisionEvent(
                action=IdentityDecisionAction.RECORD_UNLINKED,
                reason=reason,
                actor_id=actor_id,
                scope=current.scope,
                source_record_id=current.source_record_id,
                master_patient_id=current.master_patient_id,
            )
        )
        return unlinked

    def open_review(
        self,
        source: IdentityRecord,
        resolution: IdentityResolutionResult,
        *,
        actor_id: str,
    ) -> ReviewCase:
        if not resolution.requires_manual_review:
            raise ValueError("resolution does not require manual review")
        case = ReviewCase(
            source_record_id=source.record_id,
            candidate_record_ids=tuple(
                match.candidate_record_id for match in resolution.matches
            ),
            resolution_status=resolution.status,
            scope=source.scope,
        )
        self.repository.save_review_case(case)
        self.repository.append_event(
            IdentityDecisionEvent(
                action=IdentityDecisionAction.REVIEW_OPENED,
                reason=IdentityDecisionReason.ADMINISTRATIVE_CORRECTION,
                actor_id=actor_id,
                scope=source.scope,
                source_record_id=source.record_id,
                review_case_id=case.review_case_id,
            )
        )
        return case

    def approve_review_link(
        self,
        review_case_id: UUID,
        *,
        source: IdentityRecord,
        candidate_record: IdentityRecord,
        actor_id: str,
    ) -> MasterPatientLink:
        case = self._require_open_review(review_case_id, source)
        if candidate_record.record_id not in case.candidate_record_ids:
            raise ValueError("candidate record was not part of the review case")
        if candidate_record.scope != source.scope:
            raise ValueError("candidate record scope mismatch")

        candidate_link = self.repository.active_link_for_record(
            scope=candidate_record.scope,
            source_record_id=candidate_record.record_id,
            source_system=candidate_record.source_system,
        )
        if candidate_link is None:
            master = self.create_master_and_link(
                candidate_record,
                actor_id=actor_id,
                reason=IdentityDecisionReason.MANUAL_REVIEW_APPROVED,
            )
            master_patient_id = master.master_patient_id
        else:
            master_patient_id = candidate_link.master_patient_id

        link = self.link_to_master(
            master_patient_id,
            source,
            actor_id=actor_id,
            reason=IdentityDecisionReason.MANUAL_REVIEW_APPROVED,
        )
        closed = case.close(ReviewCaseStatus.APPROVED)
        self.repository.save_review_case(closed)
        self.repository.append_event(
            IdentityDecisionEvent(
                action=IdentityDecisionAction.REVIEW_APPROVED,
                reason=IdentityDecisionReason.MANUAL_REVIEW_APPROVED,
                actor_id=actor_id,
                scope=source.scope,
                source_record_id=source.record_id,
                master_patient_id=master_patient_id,
                review_case_id=review_case_id,
            )
        )
        return link

    def reject_review(
        self,
        review_case_id: UUID,
        *,
        source: IdentityRecord,
        actor_id: str,
    ) -> ReviewCase:
        case = self._require_open_review(review_case_id, source)
        closed = case.close(ReviewCaseStatus.REJECTED)
        self.repository.save_review_case(closed)
        self.repository.append_event(
            IdentityDecisionEvent(
                action=IdentityDecisionAction.REVIEW_REJECTED,
                reason=IdentityDecisionReason.MANUAL_REVIEW_REJECTED,
                actor_id=actor_id,
                scope=source.scope,
                source_record_id=source.record_id,
                review_case_id=review_case_id,
            )
        )
        return closed

    def _require_open_review(
        self,
        review_case_id: UUID,
        source: IdentityRecord,
    ) -> ReviewCase:
        case = self.repository.get_review_case(review_case_id)
        if case is None:
            raise ValueError("review case does not exist")
        if case.status is not ReviewCaseStatus.OPEN:
            raise ValueError("review case is already closed")
        if case.scope != source.scope or case.source_record_id != source.record_id:
            raise ValueError("review case does not belong to source record")
        return case

    def _link_record(
        self,
        *,
        master: MasterPatient,
        record: IdentityRecord,
        actor_id: str,
        reason: IdentityDecisionReason,
        action: IdentityDecisionAction,
    ) -> MasterPatientLink:
        link = MasterPatientLink(
            master_patient_id=master.master_patient_id,
            source_record_id=record.record_id,
            source_system=record.source_system,
            scope=record.scope,
        )
        self.repository.save_link(link)
        self.repository.append_event(
            IdentityDecisionEvent(
                action=action,
                reason=reason,
                actor_id=actor_id,
                scope=record.scope,
                source_record_id=record.record_id,
                master_patient_id=master.master_patient_id,
            )
        )
        return link
