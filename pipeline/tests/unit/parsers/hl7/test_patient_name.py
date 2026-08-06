import pytest

from healthcare_pipeline.parsers.hl7 import PatientName


def test_patient_name_normalizes_and_builds_display_name() -> None:
    name = PatientName(
        family_name=" Doe ",
        given_name=" John ",
        middle_name=" Michael ",
        prefix=" Mr ",
        suffix=" Jr ",
    )

    assert name.family_name == "Doe"
    assert name.display_name == "Mr John Michael Doe Jr"


def test_patient_name_accepts_family_name_only() -> None:
    assert PatientName(family_name="Doe").display_name == "Doe"


def test_patient_name_requires_given_or_family_name() -> None:
    with pytest.raises(ValueError, match="family name or given name"):
        PatientName(middle_name="Middle")
