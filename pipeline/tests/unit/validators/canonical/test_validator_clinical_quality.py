from datetime import UTC, datetime
from decimal import Decimal

from healthcare_pipeline.canonical import (
    CanonicalClinicalMessage,
    Coding,
    Encounter,
    EncounterClass,
    HumanName,
    Identifier,
    MedicationOrder,
    Observation,
    ObservationOrder,
    Patient,
    Period,
    Quantity,
)
from healthcare_pipeline.validators.canonical import CanonicalValidator


def _patient() -> Patient:
    return Patient(
        identifiers=(Identifier(value="123", system="urn:test:mrn"),),
        names=(HumanName(family="DOE", given=("JANE",)),),
    )


def test_validator_flags_numeric_result_without_unit() -> None:
    result = Observation(
        code=Coding(code="718-7", system="http://loinc.org"),
        values=("13.4",),
        status="F",
        value_type="NM",
    )
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-3",
        source_event_code="ORU^R01",
        patient=_patient(),
        observation_orders=(
            ObservationOrder(
                service=Coding(code="58410-2", system="http://loinc.org"),
                results=(result,),
            ),
        ),
    )

    validation = CanonicalValidator().validate(message)

    assert validation.is_valid is True
    assert any(
        issue.code == "NUMERIC_OBSERVATION_UNIT_MISSING"
        for issue in validation.warnings
    )


def test_validator_flags_reversed_medication_dose_range() -> None:
    unit = Coding(code="mg", system="http://unitsofmeasure.org")
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-4",
        source_event_code="RDE^O11",
        patient=_patient(),
        medication_orders=(
            MedicationOrder(
                medication=Coding(code="123", system="http://www.nlm.nih.gov/research/umls/rxnorm"),
                dose_minimum=Quantity(Decimal("10"), unit),
                dose_maximum=Quantity(Decimal("5"), unit),
            ),
        ),
    )

    validation = CanonicalValidator().validate(message)

    assert validation.is_valid is False
    assert any(issue.code == "DOSE_RANGE_REVERSED" for issue in validation.errors)


def test_validator_warns_when_result_falls_outside_encounter_period() -> None:
    encounter = Encounter(
        encounter_class=EncounterClass.INPATIENT,
        period=Period(
            start=datetime(2026, 8, 1, tzinfo=UTC),
            end=datetime(2026, 8, 2, tzinfo=UTC),
        ),
    )
    observation = Observation(
        code=Coding(code="718-7", system="http://loinc.org"),
        values=("13.4",),
        status="F",
        value_type="ST",
        effective_datetime=datetime(2026, 8, 3, tzinfo=UTC),
    )
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-5",
        source_event_code="ORU^R01",
        patient=_patient(),
        encounter=encounter,
        observation_orders=(
            ObservationOrder(
                service=Coding(code="58410-2", system="http://loinc.org"),
                results=(observation,),
            ),
        ),
    )

    validation = CanonicalValidator().validate(message)

    assert validation.is_valid is True
    assert any(
        issue.code == "CLINICAL_TIME_OUTSIDE_ENCOUNTER"
        for issue in validation.warnings
    )
