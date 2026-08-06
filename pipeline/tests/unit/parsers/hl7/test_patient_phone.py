import pytest

from healthcare_pipeline.parsers.hl7 import PatientPhone


def test_patient_phone_prefers_explicit_number() -> None:
    phone = PatientPhone(
        number=" +1 508 555 0100 ",
        use_code=" PRN ",
        equipment_type=" CP ",
    )

    assert phone.number == "+1 508 555 0100"
    assert phone.dialable_number == "+1 508 555 0100"


def test_patient_phone_builds_number_from_components() -> None:
    phone = PatientPhone(
        country_code="1",
        area_code="508",
        local_number="5550100",
    )

    assert phone.dialable_number == "15085550100"


def test_patient_phone_allows_email_only() -> None:
    phone = PatientPhone(email="patient@example.com")

    assert phone.email == "patient@example.com"
    assert phone.dialable_number is None


def test_patient_phone_requires_contact_value() -> None:
    with pytest.raises(ValueError, match="number, local number, or email"):
        PatientPhone(use_code="PRN")
