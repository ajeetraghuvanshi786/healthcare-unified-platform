from datetime import date, timedelta

import pytest

from healthcare_pipeline.parsers.hl7 import (
    AdministrativeSex,
    Patient,
    PatientAddress,
    PatientIdentifier,
    PatientName,
    PatientPhone,
)


def build_patient() -> Patient:
    return Patient(
        identifiers=(
            PatientIdentifier("123456", "GENERAL_HOSPITAL", "MR"),
        ),
        names=(PatientName("DOE", "JOHN"),),
        birth_date=date(1990, 1, 15),
        administrative_sex=AdministrativeSex.MALE,
        addresses=(PatientAddress(city="Boston", state_or_province="MA"),),
        phones=(PatientPhone(number="5551234567"),),
        set_id=1,
    )


def test_patient_exposes_primary_values() -> None:
    patient = build_patient()

    assert patient.primary_identifier.value == "123456"
    assert patient.official_name.display_name == "JOHN DOE"
    assert patient.administrative_sex is AdministrativeSex.MALE


def test_patient_converts_input_collections_to_tuples() -> None:
    patient = Patient(
        identifiers=[PatientIdentifier("123")],  # type: ignore[arg-type]
        names=[PatientName("Doe")],  # type: ignore[arg-type]
    )

    assert isinstance(patient.identifiers, tuple)
    assert isinstance(patient.names, tuple)


def test_patient_requires_identifier_and_name() -> None:
    with pytest.raises(ValueError, match="at least one identifier"):
        Patient(identifiers=(), names=(PatientName("Doe"),))

    with pytest.raises(ValueError, match="at least one name"):
        Patient(identifiers=(PatientIdentifier("123"),), names=())


def test_patient_rejects_future_birth_date() -> None:
    with pytest.raises(ValueError, match="must not be in the future"):
        Patient(
            identifiers=(PatientIdentifier("123"),),
            names=(PatientName("Doe"),),
            birth_date=date.today() + timedelta(days=1),
        )


def test_patient_rejects_duplicate_identifiers() -> None:
    identifier = PatientIdentifier("123", "HOSPITAL", "MR")

    with pytest.raises(ValueError, match="must not contain duplicates"):
        Patient(
            identifiers=(identifier, identifier),
            names=(PatientName("Doe"),),
        )
