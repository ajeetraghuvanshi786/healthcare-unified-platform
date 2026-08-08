from __future__ import annotations

from dataclasses import dataclass, field

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.clinical.al1_parser import AL1Parser
from healthcare_pipeline.parsers.hl7.clinical.allergy import Allergy
from healthcare_pipeline.parsers.hl7.clinical.dg1_parser import DG1Parser
from healthcare_pipeline.parsers.hl7.clinical.diagnosis import Diagnosis
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.demographics.next_of_kin import NextOfKin
from healthcare_pipeline.parsers.hl7.demographics.nk1_parser import NK1Parser
from healthcare_pipeline.parsers.hl7.demographics.patient import Patient
from healthcare_pipeline.parsers.hl7.demographics.pid_parser import PIDParser
from healthcare_pipeline.parsers.hl7.encounters.patient_encounter import PatientEncounter
from healthcare_pipeline.parsers.hl7.encounters.pv1_parser import PV1Parser
from healthcare_pipeline.parsers.hl7.financial.in1_parser import IN1Parser
from healthcare_pipeline.parsers.hl7.financial.insurance_coverage import InsuranceCoverage
from healthcare_pipeline.parsers.hl7.message_header.header import HL7MessageHeader
from healthcare_pipeline.parsers.hl7.message_header.msh_parser import MSHParser
from healthcare_pipeline.parsers.hl7.orders.common_order import CommonOrder
from healthcare_pipeline.parsers.hl7.orders.obr_parser import OBRParser
from healthcare_pipeline.parsers.hl7.orders.observation_request import ObservationRequest
from healthcare_pipeline.parsers.hl7.orders.observation_result import ObservationResult
from healthcare_pipeline.parsers.hl7.orders.obx_parser import OBXParser
from healthcare_pipeline.parsers.hl7.orders.orc_parser import ORCParser
from healthcare_pipeline.parsers.hl7.pharmacy.medication_administration import (
    MedicationAdministration,
)
from healthcare_pipeline.parsers.hl7.pharmacy.pharmacy_encoded_order import PharmacyEncodedOrder
from healthcare_pipeline.parsers.hl7.pharmacy.pharmacy_route import PharmacyRoute
from healthcare_pipeline.parsers.hl7.pharmacy.rxa_parser import RXAParser
from healthcare_pipeline.parsers.hl7.pharmacy.rxe_parser import RXEParser
from healthcare_pipeline.parsers.hl7.pharmacy.rxr_parser import RXRParser
from healthcare_pipeline.parsers.hl7.workflow.clinical_message import HL7ClinicalMessage
from healthcare_pipeline.parsers.hl7.workflow.medication_order_group import MedicationOrderGroup
from healthcare_pipeline.parsers.hl7.workflow.observation_order_group import ObservationOrderGroup
from healthcare_pipeline.parsers.hl7.workflow.workflow_type import HL7WorkflowType


@dataclass(slots=True)
class _ObservationAccumulator:
    request: ObservationRequest
    common_order: CommonOrder | None
    sequences: list[int]
    results: list[ObservationResult] = field(default_factory=list)


@dataclass(slots=True)
class _MedicationAccumulator:
    common_order: CommonOrder | None
    sequences: list[int]
    encoded_order: PharmacyEncodedOrder | None = None
    administrations: list[MedicationAdministration] = field(default_factory=list)
    routes: list[PharmacyRoute] = field(default_factory=list)


class HL7ClinicalMessageAssembler:
    """Assemble supported HL7 semantic segments in a single ordered pass.

    The assembler is stateless between calls. All mutable accumulation is local
    to ``assemble`` so one instance may safely be reused by concurrent workers
    as long as the caller does not mutate the immutable input message.
    """

    def __init__(self) -> None:
        self._msh = MSHParser()
        self._pid = PIDParser()
        self._pv1 = PV1Parser()
        self._nk1 = NK1Parser()
        self._in1 = IN1Parser()
        self._dg1 = DG1Parser()
        self._al1 = AL1Parser()
        self._orc = ORCParser()
        self._obr = OBRParser()
        self._obx = OBXParser()
        self._rxe = RXEParser()
        self._rxa = RXAParser()
        self._rxr = RXRParser()

    def assemble(self, message: HL7Message) -> HL7ClinicalMessage:
        """Create one immutable semantic aggregate from a structural message."""

        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")

        header: HL7MessageHeader | None = None
        patient: Patient | None = None
        encounter: PatientEncounter | None = None
        next_of_kin: list[NextOfKin] = []
        insurance: list[InsuranceCoverage] = []
        diagnoses: list[Diagnosis] = []
        allergies: list[Allergy] = []
        observation_groups: list[ObservationOrderGroup] = []
        medication_groups: list[MedicationOrderGroup] = []
        unattached_orders: list[CommonOrder] = []

        pending_order: tuple[CommonOrder, int] | None = None
        active_observation: _ObservationAccumulator | None = None
        active_medication: _MedicationAccumulator | None = None

        unhandled_names: list[str] = []
        unhandled_seen: set[str] = set()

        for segment in message.segments:
            name = segment.name

            if name == "MSH":
                if header is not None:
                    raise InvalidMessageError("multiple MSH segments are not supported")
                header = self._msh.parse_segment(segment, delimiters=message.delimiters)
                continue

            if name == "PID":
                if patient is not None:
                    raise InvalidMessageError(
                        "multiple PID segments require separate patient-group assembly"
                    )
                patient = self._pid.parse_segment(segment)
                continue

            if name == "PV1":
                if encounter is not None:
                    raise InvalidMessageError(
                        "multiple PV1 segments require separate encounter-group assembly"
                    )
                encounter = self._pv1.parse_segment(segment)
                continue

            if name == "NK1":
                next_of_kin.append(self._nk1.parse_segment(segment))
                continue
            if name == "IN1":
                insurance.append(self._in1.parse_segment(segment))
                continue
            if name == "DG1":
                diagnoses.append(self._dg1.parse_segment(segment))
                continue
            if name == "AL1":
                allergies.append(self._al1.parse_segment(segment))
                continue

            if name == "ORC":
                active_observation = self._flush_observation(
                    active_observation, observation_groups
                )
                active_medication = self._flush_medication(
                    active_medication, medication_groups
                )
                if pending_order is not None:
                    unattached_orders.append(pending_order[0])
                pending_order = (self._orc.parse_segment(segment), segment.sequence)
                continue

            if name == "OBR":
                active_observation = self._flush_observation(
                    active_observation, observation_groups
                )
                active_medication = self._flush_medication(
                    active_medication, medication_groups
                )
                order, order_sequence = self._consume_pending_order(pending_order)
                pending_order = None
                sequences = [segment.sequence]
                if order_sequence is not None:
                    sequences.insert(0, order_sequence)
                active_observation = _ObservationAccumulator(
                    request=self._obr.parse_segment(segment),
                    common_order=order,
                    sequences=sequences,
                )
                continue

            if name == "OBX":
                if active_observation is None:
                    raise InvalidMessageError(
                        "OBX segment is not associated with a preceding OBR segment"
                    )
                active_observation.results.append(self._obx.parse_segment(segment))
                active_observation.sequences.append(segment.sequence)
                continue

            if name == "RXE":
                active_observation = self._flush_observation(
                    active_observation, observation_groups
                )
                active_medication = self._flush_medication(
                    active_medication, medication_groups
                )
                order, order_sequence = self._consume_pending_order(pending_order)
                pending_order = None
                sequences = [segment.sequence]
                if order_sequence is not None:
                    sequences.insert(0, order_sequence)
                active_medication = _MedicationAccumulator(
                    common_order=order,
                    encoded_order=self._rxe.parse_segment(segment),
                    sequences=sequences,
                )
                continue

            if name == "RXA":
                active_observation = self._flush_observation(
                    active_observation, observation_groups
                )
                if active_medication is None:
                    order, order_sequence = self._consume_pending_order(pending_order)
                    pending_order = None
                    medication_sequences = []
                    if order_sequence is not None:
                        medication_sequences.append(order_sequence)
                    active_medication = _MedicationAccumulator(
                        common_order=order,
                        sequences=medication_sequences,
                    )
                active_medication.administrations.append(self._rxa.parse_segment(segment))
                active_medication.sequences.append(segment.sequence)
                continue

            if name == "RXR":
                active_observation = self._flush_observation(
                    active_observation, observation_groups
                )
                if active_medication is None:
                    order, order_sequence = self._consume_pending_order(pending_order)
                    pending_order = None
                    medication_sequences = []
                    if order_sequence is not None:
                        medication_sequences.append(order_sequence)
                    active_medication = _MedicationAccumulator(
                        common_order=order,
                        sequences=medication_sequences,
                    )
                active_medication.routes.append(self._rxr.parse_segment(segment))
                active_medication.sequences.append(segment.sequence)
                continue

            if name not in unhandled_seen:
                unhandled_seen.add(name)
                unhandled_names.append(name)

        active_observation = self._flush_observation(
            active_observation, observation_groups
        )
        active_medication = self._flush_medication(active_medication, medication_groups)
        if pending_order is not None:
            unattached_orders.append(pending_order[0])

        if header is None:
            raise InvalidMessageError("MSH segment is required")

        workflow_type = HL7WorkflowType.from_message_code(
            header.message_type.message_code
        )
        self._validate_workflow(
            workflow_type=workflow_type,
            patient=patient,
            observation_groups=observation_groups,
            medication_groups=medication_groups,
            unattached_orders=unattached_orders,
        )

        return HL7ClinicalMessage(
            header=header,
            workflow_type=workflow_type,
            source_segment_count=len(message.segments),
            patient=patient,
            encounter=encounter,
            next_of_kin=tuple(next_of_kin),
            insurance_coverages=tuple(insurance),
            diagnoses=tuple(diagnoses),
            allergies=tuple(allergies),
            observation_orders=tuple(observation_groups),
            medication_orders=tuple(medication_groups),
            unattached_orders=tuple(unattached_orders),
            unhandled_segment_names=tuple(unhandled_names),
        )

    @staticmethod
    def _consume_pending_order(
        pending_order: tuple[CommonOrder, int] | None,
    ) -> tuple[CommonOrder | None, int | None]:
        if pending_order is None:
            return None, None
        return pending_order

    @staticmethod
    def _flush_observation(
        accumulator: _ObservationAccumulator | None,
        destination: list[ObservationOrderGroup],
    ) -> None:
        if accumulator is None:
            return None
        destination.append(
            ObservationOrderGroup(
                request=accumulator.request,
                results=tuple(accumulator.results),
                common_order=accumulator.common_order,
                source_segment_sequences=tuple(accumulator.sequences),
            )
        )
        return None

    @staticmethod
    def _flush_medication(
        accumulator: _MedicationAccumulator | None,
        destination: list[MedicationOrderGroup],
    ) -> None:
        if accumulator is None:
            return None
        try:
            destination.append(
                MedicationOrderGroup(
                    encoded_order=accumulator.encoded_order,
                    administrations=tuple(accumulator.administrations),
                    routes=tuple(accumulator.routes),
                    common_order=accumulator.common_order,
                    source_segment_sequences=tuple(accumulator.sequences),
                )
            )
        except ValueError as exc:
            raise InvalidMessageError(
                f"incomplete medication segment group: {exc}"
            ) from exc
        return None

    @staticmethod
    def _validate_workflow(
        *,
        workflow_type: HL7WorkflowType,
        patient: Patient | None,
        observation_groups: list[ObservationOrderGroup],
        medication_groups: list[MedicationOrderGroup],
        unattached_orders: list[CommonOrder],
    ) -> None:
        if workflow_type is not HL7WorkflowType.GENERIC and patient is None:
            raise InvalidMessageError(
                f"{workflow_type.value} workflow requires a PID patient segment"
            )

        if (
            workflow_type is HL7WorkflowType.CLINICAL_ORDER
            and not observation_groups
            and not unattached_orders
        ):
            raise InvalidMessageError(
                "clinical order workflow requires ORC and/or OBR order content"
            )

        if (
            workflow_type is HL7WorkflowType.OBSERVATION_RESULT
            and not observation_groups
        ):
            raise InvalidMessageError(
                "observation-result workflow requires at least one OBR group"
            )

        if workflow_type is HL7WorkflowType.PHARMACY_ORDER and not any(
            group.encoded_order is not None for group in medication_groups
        ):
            raise InvalidMessageError(
                "pharmacy-order workflow requires at least one RXE segment"
            )

        if workflow_type is HL7WorkflowType.MEDICATION_ADMINISTRATION and not any(
            group.administrations for group in medication_groups
        ):
            raise InvalidMessageError(
                "medication-administration workflow requires at least one RXA segment"
            )
