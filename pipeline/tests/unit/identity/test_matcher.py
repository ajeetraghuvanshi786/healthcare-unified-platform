from datetime import date

from healthcare_pipeline.canonical import (
    ContactPoint,
    ContactPointSystem,
    HumanName,
    Identifier,
    Patient,
)
from healthcare_pipeline.identity import (
    DeterministicPatientMatcher,
    IdentityRecord,
    IdentityResolutionStatus,
    IdentityScope,
)

SCOPE = IdentityScope("tenant-a", "enterprise-patient")


def _record(
    record_id: str,
    *,
    identifier: str,
    dob: date | None = date(1990, 1, 2),
    phone: str = "5085551212",
) -> IdentityRecord:
    return IdentityRecord(
        record_id=record_id,
        source_system="ehr",
        scope=SCOPE,
        patient=Patient(
            identifiers=(Identifier(identifier, system="HOSP-A", type_code="MR"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
            birth_date=dob,
            telecom=(ContactPoint(ContactPointSystem.PHONE, phone),),
        ),
    )


def test_scoped_identifier_is_deterministic_match() -> None:
    match = DeterministicPatientMatcher().compare(
        _record("a", identifier="123"),
        _record("b", identifier="123"),
    )
    assert match.status is IdentityResolutionStatus.DETERMINISTIC_MATCH


def test_strong_identifier_with_birth_date_conflict_is_not_auto_match() -> None:
    match = DeterministicPatientMatcher().compare(
        _record("a", identifier="123", dob=date(1990, 1, 2)),
        _record("b", identifier="123", dob=date(1980, 1, 2)),
    )
    assert match.status is IdentityResolutionStatus.CONFLICT


def test_demographics_without_shared_identifier_are_only_possible_match() -> None:
    match = DeterministicPatientMatcher().compare(
        _record("a", identifier="123"),
        _record("b", identifier="999"),
    )
    assert match.status is IdentityResolutionStatus.POSSIBLE_MATCH
