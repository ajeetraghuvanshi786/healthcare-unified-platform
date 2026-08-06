from datetime import datetime

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, PatientClass, PV1Parser


def _message(pv1: str) -> bytes:
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        "PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        f"{pv1}"
    ).encode()


def test_pv1_parser_maps_encounter_fields() -> None:
    fields = [""] * 46
    fields[0] = "PV1"
    fields[1] = "1"
    fields[2] = "I"
    fields[3] = "ICU^101^A^GENERAL_HOSPITAL^^^MAIN^1"
    fields[6] = "WARD^50^B^GENERAL_HOSPITAL"
    fields[7] = "111^SMITH^JOHN^^^^MD^^NPI^^^^NPI"
    fields[8] = "222^JONES^MARY^^^^MD^^NPI^^^^NPI"
    fields[9] = "333^BROWN^LEE^^^^MD^^NPI^^^^NPI"
    fields[10] = "MED"
    fields[14] = "E"
    fields[18] = "ADULT"
    fields[19] = "V100^^^GENERAL_HOSPITAL^VN"
    fields[20] = "PPO^Preferred"
    fields[36] = "01"
    fields[39] = "GENERAL_HOSPITAL"
    fields[44] = "202608061030-0400"
    fields[45] = "202608071200-0400"

    encounter = PV1Parser().parse_message(
        HL7Parser().parse_message(_message("|".join(fields)))
    )

    assert encounter.patient_class is PatientClass.INPATIENT
    assert encounter.assigned_location is not None
    assert encounter.assigned_location.point_of_care == "ICU"
    assert encounter.attending_provider is not None
    assert encounter.attending_provider.family_name == "SMITH"
    assert encounter.visit_number is not None
    assert encounter.visit_number.value == "V100"
    assert encounter.financial_class == "PPO"
    assert encounter.admit_datetime == datetime(
        2026,
        8,
        6,
        10,
        30,
        tzinfo=encounter.admit_datetime.tzinfo,
    )
    assert encounter.discharge_datetime is not None


def test_pv1_parser_rejects_discharge_before_admission() -> None:
    fields = [""] * 46
    fields[0] = "PV1"
    fields[1] = "1"
    fields[2] = "I"
    fields[44] = "202608071200"
    fields[45] = "202608061200"

    with pytest.raises(InvalidMessageError, match="must not precede"):
        PV1Parser().parse_message(HL7Parser().parse_message(_message("|".join(fields))))


def test_pv1_parser_rejects_missing_segment() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN"
    )
    with pytest.raises(InvalidMessageError, match="PV1 segment"):
        PV1Parser().parse_message(HL7Parser().parse_message(payload))
