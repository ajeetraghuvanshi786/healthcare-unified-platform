from datetime import date

import pytest

from healthcare_pipeline.canonical import (
    AdministrativeGender,
    Encounter,
    EncounterClass,
    HumanName,
    Identifier,
    Patient,
)


def test_patient_is_immutable_typed_and_deduplicates_identifiers() -> None:
    patient = Patient(
        identifiers=(Identifier("123", system="FAC", type_code="MR"),),
        names=(HumanName(family="DOE", given=("JANE",)),),
        birth_date=date(1990, 1, 15),
        administrative_gender=AdministrativeGender.FEMALE,
    )

    assert patient.primary_identifier.value == "123"

    with pytest.raises(ValueError, match="duplicates"):
        Patient(
            identifiers=(
                Identifier("123", system="FAC", type_code="MR"),
                Identifier("123", system="fac", type_code="mr"),
            ),
            names=(HumanName(family="DOE"),),
        )


def test_encounter_accepts_source_neutral_classification() -> None:
    encounter = Encounter(encounter_class=EncounterClass.INPATIENT)
    assert encounter.encounter_class is EncounterClass.INPATIENT
