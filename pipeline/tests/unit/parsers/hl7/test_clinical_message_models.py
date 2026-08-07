from healthcare_pipeline.parsers.hl7 import HL7WorkflowType


def test_workflow_type_classifies_supported_message_families() -> None:
    assert HL7WorkflowType.from_message_code("ADT") is HL7WorkflowType.ADT
    assert HL7WorkflowType.from_message_code("orm") is HL7WorkflowType.CLINICAL_ORDER
    assert HL7WorkflowType.from_message_code("ORU") is HL7WorkflowType.OBSERVATION_RESULT
    assert HL7WorkflowType.from_message_code("RDE") is HL7WorkflowType.PHARMACY_ORDER
    assert (
        HL7WorkflowType.from_message_code("RAS")
        is HL7WorkflowType.MEDICATION_ADMINISTRATION
    )
    assert HL7WorkflowType.from_message_code("MDM") is HL7WorkflowType.GENERIC
