from importlib import import_module


def test_public_hl7_api_remains_importable() -> None:
    package = import_module("healthcare_pipeline.parsers.hl7")
    expected = (
        "HL7Parser",
        "HL7ClinicalMessageAssembler",
        "PIDParser",
        "PV1Parser",
        "AL1Parser",
        "ORCParser",
        "OBRParser",
        "OBXParser",
        "RXAParser",
        "RXEParser",
        "RXRParser",
    )
    for name in expected:
        assert hasattr(package, name)


def test_legacy_module_paths_remain_compatible() -> None:
    legacy_patient = import_module("healthcare_pipeline.parsers.hl7.patient")
    modular_patient = import_module(
        "healthcare_pipeline.parsers.hl7.demographics.patient"
    )
    assert legacy_patient.Patient is modular_patient.Patient

    legacy_workflow = import_module(
        "healthcare_pipeline.parsers.hl7.clinical_message_assembler"
    )
    modular_workflow = import_module(
        "healthcare_pipeline.parsers.hl7.workflow.clinical_message_assembler"
    )
    assert (
        legacy_workflow.HL7ClinicalMessageAssembler
        is modular_workflow.HL7ClinicalMessageAssembler
    )


def test_major_subpackages_are_importable() -> None:
    for name in (
        "core",
        "datatypes",
        "mapping",
        "message_header",
        "demographics",
        "encounters",
        "financial",
        "clinical",
        "orders",
        "pharmacy",
        "workflow",
    ):
        import_module(f"healthcare_pipeline.parsers.hl7.{name}")
