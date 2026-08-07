from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.allergy import Allergy
from healthcare_pipeline.parsers.hl7.common_order import CommonOrder
from healthcare_pipeline.parsers.hl7.diagnosis import Diagnosis
from healthcare_pipeline.parsers.hl7.header import HL7MessageHeader
from healthcare_pipeline.parsers.hl7.insurance_coverage import InsuranceCoverage
from healthcare_pipeline.parsers.hl7.medication_order_group import MedicationOrderGroup
from healthcare_pipeline.parsers.hl7.next_of_kin import NextOfKin
from healthcare_pipeline.parsers.hl7.observation_order_group import ObservationOrderGroup
from healthcare_pipeline.parsers.hl7.patient import Patient
from healthcare_pipeline.parsers.hl7.patient_encounter import PatientEncounter
from healthcare_pipeline.parsers.hl7.workflow_type import HL7WorkflowType


@dataclass(frozen=True, slots=True)
class HL7ClinicalMessage:
    """Immutable semantic aggregate for one structurally parsed HL7 v2 message.

    Raw PHI is intentionally not duplicated here. The immutable raw ingestion
    record remains the audit source of truth while this object carries only the
    typed semantics required by downstream validation and transformation.
    """

    header: HL7MessageHeader
    workflow_type: HL7WorkflowType
    source_segment_count: int
    patient: Patient | None = None
    encounter: PatientEncounter | None = None
    next_of_kin: tuple[NextOfKin, ...] = ()
    insurance_coverages: tuple[InsuranceCoverage, ...] = ()
    diagnoses: tuple[Diagnosis, ...] = ()
    allergies: tuple[Allergy, ...] = ()
    observation_orders: tuple[ObservationOrderGroup, ...] = ()
    medication_orders: tuple[MedicationOrderGroup, ...] = ()
    unattached_orders: tuple[CommonOrder, ...] = ()
    unhandled_segment_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.header, HL7MessageHeader):
            raise TypeError("header must be an HL7MessageHeader")
        if not isinstance(self.workflow_type, HL7WorkflowType):
            raise TypeError("workflow_type must be an HL7WorkflowType")
        if not isinstance(self.source_segment_count, int) or self.source_segment_count < 1:
            raise ValueError("source_segment_count must be a positive integer")
        if self.patient is not None and not isinstance(self.patient, Patient):
            raise TypeError("patient must be a Patient or None")
        if self.encounter is not None and not isinstance(self.encounter, PatientEncounter):
            raise TypeError("encounter must be a PatientEncounter or None")

        for field_name, expected_type in (
            ("next_of_kin", NextOfKin),
            ("insurance_coverages", InsuranceCoverage),
            ("diagnoses", Diagnosis),
            ("allergies", Allergy),
            ("observation_orders", ObservationOrderGroup),
            ("medication_orders", MedicationOrderGroup),
            ("unattached_orders", CommonOrder),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)

        names = tuple(self.unhandled_segment_names)
        if any(
            not isinstance(value, str)
            or len(value) != 3
            or not value.isalnum()
            or value != value.upper()
            for value in names
        ):
            raise ValueError("unhandled_segment_names must contain HL7 segment names")
        if len(names) != len(set(names)):
            raise ValueError("unhandled_segment_names must not contain duplicates")
        object.__setattr__(self, "unhandled_segment_names", names)

    @property
    def message_control_id(self) -> str:
        """Return MSH-10, the sender-assigned message control identifier."""

        return self.header.message_control_id

    @property
    def event_code(self) -> str:
        """Return the combined MSH-9 message and trigger event code."""

        return self.header.message_type.event_code
