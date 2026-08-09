from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class PatientContextRule:
    """Require patient context when patient-specific clinical resources are present."""

    rule_id: str = "canonical.patient-context"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        has_patient_specific_content = any(
            (
                message.encounter is not None,
                bool(message.coverages),
                bool(message.diagnoses),
                bool(message.allergies),
                bool(message.observation_orders),
                bool(message.medication_orders),
                bool(message.medication_administrations),
            )
        )
        if has_patient_specific_content and message.patient is None:
            return (
                ValidationIssue(
                    code="PATIENT_CONTEXT_REQUIRED",
                    message="Patient context is required when patient-specific resources exist.",
                    severity=ValidationSeverity.ERROR,
                    path="patient",
                    rule_id=self.rule_id,
                ),
            )
        return ()


@dataclass(frozen=True, slots=True)
class EncounterContextRule:
    """Flag missing encounter context for encounter-oriented clinical activity."""

    rule_id: str = "canonical.encounter-context"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        if message.encounter is not None:
            return ()
        if message.observation_orders or message.medication_administrations:
            return (
                ValidationIssue(
                    code="ENCOUNTER_CONTEXT_MISSING",
                    message=(
                        "Encounter context is absent for clinical activity; "
                        "verify whether the source workflow is encounter-based."
                    ),
                    severity=ValidationSeverity.WARNING,
                    path="encounter",
                    rule_id=self.rule_id,
                ),
            )
        return ()
