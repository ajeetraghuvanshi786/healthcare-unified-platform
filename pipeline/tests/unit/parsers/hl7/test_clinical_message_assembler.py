import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import (
    HL7ClinicalMessageAssembler,
    HL7Parser,
    HL7WorkflowType,
)


def _parse(payload: bytes):  # type: ignore[no-untyped-def]
    return HL7ClinicalMessageAssembler().assemble(HL7Parser().parse_message(payload))


def test_assembler_builds_adt_patient_context() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608071000||ADT^A01|ADT-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN||19800101|M\r"
        b"PV1|1|I|ICU^101^A^HOSPITAL\r"
        b"NK1|1|DOE^JANE|SPO^Spouse^HL70063\r"
        b"IN1|1|PPO^Preferred^LOCAL||ACME HEALTH\r"
        b"DG1|1|ICD10|I10^Essential hypertension^ICD-10-CM\r"
        b"AL1|1|DA^Drug allergy^HL70127|7980^Penicillin^RXNORM\r"
        b"EVN|A01|202608071000"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.ADT
    assert message.patient is not None
    assert message.patient.primary_identifier.value == "123"
    assert message.encounter is not None
    assert len(message.next_of_kin) == 1
    assert len(message.insurance_coverages) == 1
    assert len(message.diagnoses) == 1
    assert len(message.allergies) == 1
    assert message.unhandled_segment_names == ("EVN",)
    assert message.message_control_id == "ADT-1"
    assert message.event_code == "ADT^A01"


def test_assembler_groups_oru_order_request_and_results() -> None:
    payload = (
        b"MSH|^~\\&|LAB|HOSPITAL|EHR|HOSPITAL|202608071000||ORU^R01|ORU-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"ORC|RE|P100^PLACER|F200^FILLER\r"
        b"OBR|1|P100^PLACER|F200^FILLER|58410-2^CBC panel^LN\r"
        b"OBX|1|NM|718-7^Hemoglobin^LN||13.4|g/dL^grams per deciliter^UCUM|12-16|N|||F\r"
        b"OBX|2|NM|6690-2^Leukocytes^LN||6.2|10*3/uL^10*3/uL^UCUM|4-11|N|||F"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.OBSERVATION_RESULT
    assert len(message.observation_orders) == 1
    group = message.observation_orders[0]
    assert group.common_order is not None
    assert group.common_order.order_control == "RE"
    assert group.request.universal_service_identifier.identifier == "58410-2"
    assert len(group.results) == 2
    assert group.results[0].observation_identifier.identifier == "718-7"
    assert group.source_segment_sequences == (3, 4, 5, 6)
    assert group.has_results is True


def test_assembler_builds_orm_order_without_results() -> None:
    payload = (
        b"MSH|^~\\&|EHR|HOSPITAL|LAB|HOSPITAL|202608071000||ORM^O01|ORM-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"ORC|NW|P100^PLACER\r"
        b"OBR|1|P100^PLACER||24323-8^Basic metabolic panel^LN"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.CLINICAL_ORDER
    assert len(message.observation_orders) == 1
    assert message.observation_orders[0].results == ()


def test_assembler_groups_pharmacy_encoded_order_and_route() -> None:
    payload = (
        b"MSH|^~\\&|EHR|HOSPITAL|PHARM|HOSPITAL|202608071000||RDE^O11|RDE-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"ORC|NW|P500^PLACER\r"
        b"RXE|1^BID|860975^Metformin 500 MG tablet^RXNORM|1|1|TAB^tablet^L\r"
        b"RXR|PO^Oral^HL70162"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.PHARMACY_ORDER
    assert len(message.medication_orders) == 1
    group = message.medication_orders[0]
    assert group.common_order is not None
    assert group.encoded_order is not None
    assert group.encoded_order.give_code.identifier == "860975"
    assert group.routes[0].route.identifier == "PO"
    assert group.administrations == ()


def test_assembler_groups_medication_administration_and_route() -> None:
    payload = (
        b"MSH|^~\\&|MAR|HOSPITAL|EHR|HOSPITAL|202608071000||RAS^O17|RAS-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"ORC|RE|P500^PLACER\r"
        b"RXA|0|1|202608071000||860975^Metformin^RXNORM|1|TAB^tablet^L\r"
        b"RXR|PO^Oral^HL70162"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.MEDICATION_ADMINISTRATION
    assert len(message.medication_orders) == 1
    group = message.medication_orders[0]
    assert len(group.administrations) == 1
    assert group.administrations[0].administered_code.identifier == "860975"
    assert group.routes[0].route.identifier == "PO"


def test_assembler_rejects_orphan_obx() -> None:
    payload = (
        b"MSH|^~\\&|LAB|HOSPITAL|EHR|HOSPITAL|202608071000||ORU^R01|ORU-2|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"OBX|1|ST|NOTE^Comment^L||Unexpected result||||||F"
    )

    with pytest.raises(InvalidMessageError, match="preceding OBR"):
        _parse(payload)


def test_assembler_rejects_multiple_patient_groups() -> None:
    payload = (
        b"MSH|^~\\&|EHR|HOSPITAL|HIE|HOSPITAL|202608071000||ADT^A01|ADT-2|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"PID|1||456^^^HOSPITAL^MR||SMITH^JANE"
    )

    with pytest.raises(InvalidMessageError, match="multiple PID"):
        _parse(payload)


def test_generic_workflow_can_preserve_unhandled_segment_visibility() -> None:
    payload = (
        b"MSH|^~\\&|EHR|HOSPITAL|DOC|HOSPITAL|202608071000||MDM^T02|MDM-1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        b"TXA|1|DS|TEXT"
    )

    message = _parse(payload)

    assert message.workflow_type is HL7WorkflowType.GENERIC
    assert message.unhandled_segment_names == ("TXA",)
