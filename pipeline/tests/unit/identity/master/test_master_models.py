from datetime import UTC, datetime, timedelta

import pytest

from healthcare_pipeline.identity import (
    IdentityResolutionStatus,
    IdentityScope,
    MasterPatient,
    MasterPatientLink,
    MasterPatientLinkStatus,
    ReviewCase,
    ReviewCaseStatus,
)


def test_master_patient_is_scoped_and_immutable() -> None:
    master = MasterPatient(scope=IdentityScope("tenant-a", "enterprise"))
    assert master.scope.tenant_id == "tenant-a"
    with pytest.raises(AttributeError):
        master.scope = IdentityScope("tenant-b", "enterprise")  # type: ignore[misc]


def test_link_unlink_is_reversible_without_deleting_history() -> None:
    scope = IdentityScope("tenant-a", "enterprise")
    master = MasterPatient(scope=scope)
    linked_at = datetime.now(UTC)
    link = MasterPatientLink(
        master_patient_id=master.master_patient_id,
        source_record_id="record-1",
        source_system="epic",
        scope=scope,
        linked_at=linked_at,
    )
    unlinked = link.unlink(at=linked_at + timedelta(seconds=1))

    assert link.status is MasterPatientLinkStatus.ACTIVE
    assert unlinked.status is MasterPatientLinkStatus.UNLINKED
    assert unlinked.unlinked_at is not None


def test_review_case_only_accepts_reviewable_resolution() -> None:
    with pytest.raises(ValueError, match="reviewable"):
        ReviewCase(
            source_record_id="record-1",
            candidate_record_ids=(),
            resolution_status=IdentityResolutionStatus.NO_MATCH,
            scope=IdentityScope("tenant-a", "enterprise"),
        )


def test_review_case_close_is_one_way() -> None:
    case = ReviewCase(
        source_record_id="record-1",
        candidate_record_ids=("record-2",),
        resolution_status=IdentityResolutionStatus.POSSIBLE_MATCH,
        scope=IdentityScope("tenant-a", "enterprise"),
    )
    closed = case.close(ReviewCaseStatus.REJECTED)
    assert closed.status is ReviewCaseStatus.REJECTED
    with pytest.raises(ValueError, match="already closed"):
        closed.close(ReviewCaseStatus.APPROVED)
