import pytest

from healthcare_pipeline.parsers.hl7 import PatientIdentifier


def test_patient_identifier_normalizes_values() -> None:
    identifier = PatientIdentifier(
        value=" 123456 ",
        assigning_authority=" General_Hospital ",
        identifier_type=" mr ",
    )

    assert identifier.value == "123456"
    assert identifier.assigning_authority == "General_Hospital"
    assert identifier.identifier_type == "mr"
    assert identifier.is_scoped is True
    assert identifier.identity_key == ("general_hospital", "123456", "MR")


def test_patient_identifier_allows_legacy_unscoped_identifier() -> None:
    identifier = PatientIdentifier(value="123")

    assert identifier.is_scoped is False
    assert identifier.identity_key == (None, "123", None)


def test_patient_identifier_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="value must not be blank"):
        PatientIdentifier(value=" ")


def test_patient_identifier_is_immutable() -> None:
    identifier = PatientIdentifier(value="123")

    with pytest.raises(AttributeError):
        identifier.value = "456"  # type: ignore[misc]
