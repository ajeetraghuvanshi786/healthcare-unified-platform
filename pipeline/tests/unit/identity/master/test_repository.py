import pytest

from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import (
    IdentityScope,
    InMemoryMasterIdentityRepository,
    MasterPatient,
    MasterPatientLink,
)


def _patient(value: str) -> Patient:
    return Patient(
        identifiers=(Identifier(value=value, system="hospital-a"),),
        names=(HumanName(family="Doe", given=("Jane",)),),
    )


def test_repository_prevents_one_source_record_from_linking_to_two_masters() -> None:
    scope = IdentityScope("tenant-a", "enterprise")
    repository = InMemoryMasterIdentityRepository()
    first = MasterPatient(scope=scope)
    second = MasterPatient(scope=scope)
    repository.create_master(first)
    repository.create_master(second)

    repository.save_link(
        MasterPatientLink(
            master_patient_id=first.master_patient_id,
            source_record_id="record-1",
            source_system="epic",
            scope=scope,
        )
    )

    with pytest.raises(ValueError, match="already linked"):
        repository.save_link(
            MasterPatientLink(
                master_patient_id=second.master_patient_id,
                source_record_id="record-1",
                source_system="epic",
                scope=scope,
            )
        )


def test_repository_rejects_cross_scope_link() -> None:
    repository = InMemoryMasterIdentityRepository()
    master = MasterPatient(scope=IdentityScope("tenant-a", "enterprise"))
    repository.create_master(master)
    with pytest.raises(ValueError, match="scope"):
        repository.save_link(
            MasterPatientLink(
                master_patient_id=master.master_patient_id,
                source_record_id="record-1",
                source_system="epic",
                scope=IdentityScope("tenant-b", "enterprise"),
            )
        )
