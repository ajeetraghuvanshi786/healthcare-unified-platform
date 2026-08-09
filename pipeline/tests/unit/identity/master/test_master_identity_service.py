import pytest

from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import (
    IdentityCandidateMatch,
    IdentityDecisionReason,
    IdentityRecord,
    IdentityResolutionResult,
    IdentityResolutionStatus,
    IdentityScope,
    InMemoryMasterIdentityRepository,
    MasterPatientIdentityService,
    MasterPatientLinkStatus,
    ReviewCaseStatus,
)


def _record(record_id: str, mrn: str, *, tenant: str = "tenant-a") -> IdentityRecord:
    return IdentityRecord(
        record_id=record_id,
        source_system="epic",
        scope=IdentityScope(tenant, "enterprise"),
        patient=Patient(
            identifiers=(Identifier(value=mrn, system="hospital-a"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
        ),
    )


def test_service_creates_master_and_idempotently_links_record() -> None:
    repository = InMemoryMasterIdentityRepository()
    service = MasterPatientIdentityService(repository)
    record = _record("record-1", "MRN-1")

    first = service.create_master_and_link(record, actor_id="system")
    second = service.create_master_and_link(record, actor_id="system")

    assert first.master_patient_id == second.master_patient_id
    assert len(repository.active_links_for_master(first.master_patient_id)) == 1


def test_service_prohibits_cross_scope_link() -> None:
    repository = InMemoryMasterIdentityRepository()
    service = MasterPatientIdentityService(repository)
    first = _record("record-1", "MRN-1")
    second = _record("record-2", "MRN-2", tenant="tenant-b")
    master = service.create_master_and_link(first, actor_id="system")

    with pytest.raises(ValueError, match="cross-scope"):
        service.link_to_master(
            master.master_patient_id,
            second,
            actor_id="reviewer",
            reason=IdentityDecisionReason.MANUAL_REVIEW_APPROVED,
        )


def test_unlink_preserves_audit_and_removes_active_link() -> None:
    repository = InMemoryMasterIdentityRepository()
    service = MasterPatientIdentityService(repository)
    record = _record("record-1", "MRN-1")
    master = service.create_master_and_link(record, actor_id="system")

    unlinked = service.unlink_record(
        scope=record.scope,
        source_record_id=record.record_id,
        actor_id="reviewer-1",
        reason=IdentityDecisionReason.WRONG_PATIENT_LINK,
    )

    assert unlinked.status is MasterPatientLinkStatus.UNLINKED
    assert repository.active_link_for_record(
        scope=record.scope,
        source_record_id=record.record_id,
    ) is None
    assert len(repository.events()) == 2
    assert repository.active_links_for_master(master.master_patient_id) == ()


def test_possible_match_requires_review_before_link() -> None:
    repository = InMemoryMasterIdentityRepository()
    service = MasterPatientIdentityService(repository)
    source = _record("source", "MRN-NEW")
    candidate = _record("candidate", "MRN-OLD")

    resolution = IdentityResolutionResult(
        status=IdentityResolutionStatus.POSSIBLE_MATCH,
        matches=(
            IdentityCandidateMatch(
                candidate_record_id=candidate.record_id,
                status=IdentityResolutionStatus.POSSIBLE_MATCH,
            ),
        ),
    )
    case = service.open_review(source, resolution, actor_id="system")
    assert case.status is ReviewCaseStatus.OPEN
    assert repository.active_link_for_record(
        scope=source.scope,
        source_record_id=source.record_id,
    ) is None

    link = service.approve_review_link(
        case.review_case_id,
        source=source,
        candidate_record=candidate,
        actor_id="reviewer-1",
    )
    assert link.status is MasterPatientLinkStatus.ACTIVE
    closed = repository.get_review_case(case.review_case_id)
    assert closed is not None
    assert closed.status is ReviewCaseStatus.APPROVED


def test_review_rejection_never_links_source() -> None:
    repository = InMemoryMasterIdentityRepository()
    service = MasterPatientIdentityService(repository)
    source = _record("source", "MRN-NEW")
    resolution = IdentityResolutionResult(
        status=IdentityResolutionStatus.CONFLICT,
        matches=(
            IdentityCandidateMatch(
                candidate_record_id="candidate",
                status=IdentityResolutionStatus.CONFLICT,
            ),
        ),
    )
    case = service.open_review(source, resolution, actor_id="system")
    rejected = service.reject_review(
        case.review_case_id,
        source=source,
        actor_id="reviewer-1",
    )

    assert rejected.status is ReviewCaseStatus.REJECTED
    assert repository.active_link_for_record(
        scope=source.scope,
        source_record_id=source.record_id,
    ) is None
