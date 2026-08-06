import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import DG1Parser, HL7Parser


def _message(dg1_segments: str) -> bytes:
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        "PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        f"{dg1_segments}"
    ).encode()


def test_dg1_parser_maps_multiple_diagnoses() -> None:
    payload = _message(
        "DG1|1|ICD10|E11.9^Type 2 diabetes mellitus^ICD-10-CM|"
        "Diabetes|202608061030|F|||||||||1|123^SMITH^JOHN^^^^MD^^NPI^^^^NPI|||"
        "202608061100\r"
        "DG1|2|ICD10|I10^Essential hypertension^ICD-10-CM|Hypertension|"
        "202608061035|W|||||||||2"
    )

    diagnoses = DG1Parser().parse_message(HL7Parser().parse_message(payload))

    assert len(diagnoses) == 2
    assert diagnoses[0].code.identifier == "E11.9"
    assert diagnoses[0].code.coding_system == "ICD-10-CM"
    assert diagnoses[0].priority == 1
    assert diagnoses[0].diagnosing_providers[0].family_name == "SMITH"
    assert diagnoses[1].diagnosis_type == "W"


def test_dg1_parser_requires_diagnosis_code() -> None:
    with pytest.raises(InvalidMessageError, match="diagnosis code is required"):
        DG1Parser().parse_message(HL7Parser().parse_message(_message("DG1|1|ICD10||")))


def test_dg1_parser_rejects_invalid_priority() -> None:
    fields = [""] * 16
    fields[0] = "DG1"
    fields[1] = "1"
    fields[3] = "E11.9^Diabetes^ICD-10-CM"
    fields[15] = "0"
    with pytest.raises(InvalidMessageError, match="greater than zero"):
        DG1Parser().parse_message(
            HL7Parser().parse_message(_message("|".join(fields)))
        )
