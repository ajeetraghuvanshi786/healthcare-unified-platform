from healthcare_pipeline.canonical import (
    CanonicalClinicalMessage,
    Coding,
    Diagnosis,
    HumanName,
    Identifier,
    Patient,
)
from healthcare_pipeline.validators.canonical import CanonicalValidator


def test_validator_requires_patient_for_patient_specific_resources() -> None:
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-1",
        source_event_code="ORU^R01",
        diagnoses=(Diagnosis(code=Coding(code="E11.9", system="ICD-10-CM")),),
    )

    result = CanonicalValidator().validate(message)

    assert result.is_valid is False
    assert any(issue.code == "PATIENT_CONTEXT_REQUIRED" for issue in result.errors)


def test_validator_warns_about_unscoped_patient_identifier() -> None:
    patient = Patient(
        identifiers=(Identifier(value="12345"),),
        names=(HumanName(family="DOE", given=("JANE",)),),
    )
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-2",
        source_event_code="ADT^A01",
        patient=patient,
    )

    result = CanonicalValidator().validate(message)

    assert result.is_valid is True
    assert any(issue.code == "IDENTIFIER_SCOPE_MISSING" for issue in result.warnings)
