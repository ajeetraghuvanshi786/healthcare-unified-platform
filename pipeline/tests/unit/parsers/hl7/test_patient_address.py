import pytest

from healthcare_pipeline.parsers.hl7 import PatientAddress


def test_patient_address_normalizes_and_formats() -> None:
    address = PatientAddress(
        street_address=" 123 Main St ",
        city=" Boston ",
        state_or_province=" MA ",
        postal_code=" 02115 ",
        country=" USA ",
    )

    assert address.street_address == "123 Main St"
    assert address.single_line == "123 Main St, Boston, MA, 02115, USA"


def test_patient_address_requires_at_least_one_value() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        PatientAddress()
