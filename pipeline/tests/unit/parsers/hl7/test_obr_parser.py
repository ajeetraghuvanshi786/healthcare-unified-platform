from datetime import UTC, datetime

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, OBRParser


def test_obr_parser_maps_observation_request() -> None:
    fields = [""] * 31
    fields[0] = "1"
    fields[1] = "P100^PLACER"
    fields[2] = "F200^FILLER"
    fields[3] = "718-7^Hemoglobin^LN"
    fields[5] = "202608061000"
    fields[6] = "202608061015"
    fields[7] = "202608061020"
    fields[9] = "111^COLLECTOR^CARL"
    fields[12] = "Fatigue"
    fields[13] = "202608061030"
    fields[14] = "BLD^Whole blood^HL70070"
    fields[15] = "222^SMITH^JANE"
    fields[21] = "202608061145"
    fields[23] = "LAB"
    fields[24] = "F"
    fields[26] = "1^ONCE"
    fields[27] = "333^JONES^ROBERT"
    fields[30] = "R53.83^Fatigue^ICD-10-CM"
    segment = "OBR|" + "|".join(fields)
    payload = (
        "MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORU^R01|1|P|2.5\r"
        + segment
    ).encode()

    request = OBRParser().parse_message(HL7Parser().parse_message(payload))[0]

    assert request.universal_service_identifier.identifier == "718-7"
    assert request.observation_datetime == datetime(2026, 8, 6, 10, 15, tzinfo=UTC)
    assert request.result_status == "F"
    assert request.reasons_for_study[0].identifier == "R53.83"


def test_obr_parser_requires_service_identifier() -> None:
    payload = b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORU^R01|1|P|2.5\rOBR|1|P100|F200|"

    with pytest.raises(InvalidMessageError, match="service identifier is required"):
        OBRParser().parse_message(HL7Parser().parse_message(payload))
