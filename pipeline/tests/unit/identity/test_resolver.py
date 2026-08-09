from datetime import date

from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import (
    HmacIdentityKeyEncoder,
    IdentityRecord,
    IdentityResolutionStatus,
    IdentityScope,
    InMemoryIdentityCandidateStore,
    PatientIdentityService,
)

SCOPE = IdentityScope("tenant-a", "enterprise-patient")


def _record(record_id: str, mrn: str, dob: date = date(1990, 1, 2)) -> IdentityRecord:
    return IdentityRecord(
        record_id=record_id,
        source_system="ehr-a",
        scope=SCOPE,
        patient=Patient(
            identifiers=(Identifier(mrn, system="HOSP-A", type_code="MR"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
            birth_date=dob,
        ),
    )


def test_unique_deterministic_match_selects_record_without_merging() -> None:
    store = InMemoryIdentityCandidateStore(HmacIdentityKeyEncoder(b"k" * 32))
    service = PatientIdentityService.create(store)
    service.index(_record("existing", "123"))

    result = service.resolve(_record("incoming", "123"))

    assert result.status is IdentityResolutionStatus.DETERMINISTIC_MATCH
    assert result.selected_record_id == "existing"
    assert store.get("incoming") is None


def test_duplicate_strong_identifier_is_ambiguous_not_arbitrarily_selected() -> None:
    store = InMemoryIdentityCandidateStore(HmacIdentityKeyEncoder(b"k" * 32))
    service = PatientIdentityService.create(store)
    service.index(_record("one", "123"))
    service.index(_record("two", "123"))

    result = service.resolve(_record("incoming", "123"))

    assert result.status is IdentityResolutionStatus.AMBIGUOUS
    assert result.selected_record_id is None
    assert {match.candidate_record_id for match in result.matches} == {"one", "two"}


def test_no_candidate_returns_no_match() -> None:
    store = InMemoryIdentityCandidateStore(HmacIdentityKeyEncoder(b"k" * 32))
    service = PatientIdentityService.create(store)

    result = service.resolve(_record("incoming", "123"))

    assert result.status is IdentityResolutionStatus.NO_MATCH
