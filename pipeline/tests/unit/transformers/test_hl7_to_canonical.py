from datetime import date

from healthcare_pipeline.canonical import AdministrativeGender, EncounterClass
from healthcare_pipeline.parsers.hl7 import HL7ClinicalMessageAssembler, HL7Parser
from healthcare_pipeline.transformers import HL7ToCanonicalTransformer


def _adt_message() -> bytes:
    fields = [""] * 20
    fields[0] = "PV1"
    fields[1] = "1"
    fields[2] = "I"
    fields[3] = "ICU^101^A^HOSPITAL"
    fields[7] = "111^SMITH^JOHN"
    fields[19] = "V100^^^HOSPITAL^VN"
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HIE|202608071030-0400||"
        "ADT^A01|MSG-100|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||DOE^JANE||19900115|F|||"
        "1 MAIN ST^^BOSTON^MA^02110^USA||5551234\r"
        + "|".join(fields)
    ).encode()


ORU = (
    b"MSH|^~\\&|LAB|HOSPITAL|EHR|HOSPITAL|202608071030-0400||"
    b"ORU^R01|MSG-200|P|2.5\r"
    b"PID|1||12345^^^HOSPITAL^MR||DOE^JANE\r"
    b"PV1|1|O\r"
    b"ORC|RE|PLACER1|FILLER1\r"
    b"OBR|1|PLACER1|FILLER1|718-7^Hemoglobin^LN||||"
    b"202608071000-0400||||||||||||111^SMITH^JOHN||||||F\r"
    b"OBX|1|NM|718-7^Hemoglobin^LN||13.4|"
    b"g/dL^g/dL^UCUM|12-16|N|||F"
)


def test_transformer_maps_adt_patient_and_encounter() -> None:
    structured = HL7Parser().parse_message(_adt_message())
    semantic = HL7ClinicalMessageAssembler().assemble(structured)

    result = HL7ToCanonicalTransformer().transform(semantic)

    assert result.source_format == "hl7_v2"
    assert result.source_message_id == "MSG-100"
    assert result.patient is not None
    assert result.patient.birth_date == date(1990, 1, 15)
    assert result.patient.administrative_gender is AdministrativeGender.FEMALE
    assert result.encounter is not None
    assert result.encounter.encounter_class is EncounterClass.INPATIENT
    assert result.encounter.identifiers[0].value == "V100"


def test_transformer_maps_oru_order_and_observation() -> None:
    structured = HL7Parser().parse_message(ORU)
    semantic = HL7ClinicalMessageAssembler().assemble(structured)

    result = HL7ToCanonicalTransformer().transform(semantic)

    assert len(result.observation_orders) == 1
    order = result.observation_orders[0]
    assert order.service.code == "718-7"
    assert len(order.results) == 1
    assert order.results[0].values == ("13.4",)
    assert order.results[0].units is not None
    assert order.results[0].units.system == "UCUM"
