from healthcare_pipeline.canonical import (
    CanonicalClinicalMessage,
    Coding,
    Diagnosis,
    HumanName,
    Identifier,
    Patient,
)
from healthcare_pipeline.terminology import (
    LOINC,
    CanonicalTerminologyService,
    StaticTerminologyProvider,
    TerminologyResolutionStatus,
    TerminologyService,
)


def _patient() -> Patient:
    return Patient(
        identifiers=(Identifier(value="123", system="urn:mrn:test"),),
        names=(HumanName(family="Doe", given=("Jane",)),),
    )


def test_canonical_service_assesses_codings_by_structural_path() -> None:
    provider = StaticTerminologyProvider(
        name="local-loinc",
        code_sets={LOINC.canonical_uri: frozenset({"718-7"})},
    )
    service = CanonicalTerminologyService(
        terminology=TerminologyService(providers=(provider,))
    )
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-1",
        source_event_code="ORU^R01",
        patient=_patient(),
        diagnoses=(
            Diagnosis(code=Coding(code="718-7", display="Hemoglobin", system="LN")),
        ),
    )

    assessments = service.assess_message(message)

    assert len(assessments) == 1
    assert assessments[0].path == "diagnoses[0].code"
    assert assessments[0].normalized.status is TerminologyResolutionStatus.NORMALIZED
    assert assessments[0].normalized.coding.system == LOINC.canonical_uri


def test_canonical_service_enforces_assessment_bound() -> None:
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-2",
        source_event_code="ADT^A01",
        patient=_patient(),
        diagnoses=(
            Diagnosis(code=Coding(code="A", system="LOCAL")),
            Diagnosis(code=Coding(code="B", system="LOCAL")),
        ),
    )

    assessments = CanonicalTerminologyService(max_assessments=1).assess_message(message)

    assert len(assessments) == 1
