import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, IN1Parser


def _message(in1_segments: str) -> bytes:
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        "PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        f"{in1_segments}"
    ).encode()


def _in1() -> str:
    fields = [""] * 50
    fields[0] = "IN1"
    fields[1] = "1"
    fields[2] = "PPO^Preferred Plan^LOCAL"
    fields[3] = "INS001^^^PAYER^XX"
    fields[4] = "ACME HEALTH"
    fields[5] = "100 INSURANCE WAY^^BOSTON^MA^02110"
    fields[6] = "AGENT^ALICE"
    fields[7] = "8005550100^WPN^PH"
    fields[8] = "GRP-100"
    fields[9] = "EMPLOYEE GROUP"
    fields[12] = "20260101"
    fields[13] = "20261231"
    fields[15] = "PPO"
    fields[16] = "DOE^JOHN"
    fields[17] = "SEL^Self^HL70063"
    fields[18] = "19900115"
    fields[19] = "1 MAIN ST^^BOSTON^MA^02110"
    fields[36] = "POL-900"
    fields[49] = "MEM-123^^^ACME^MB"
    return "|".join(fields)


def test_in1_parser_maps_coverage() -> None:
    coverages = IN1Parser().parse_message(HL7Parser().parse_message(_message(_in1())))

    assert len(coverages) == 1
    coverage = coverages[0]
    assert coverage.company_name == "ACME HEALTH"
    assert coverage.group_number == "GRP-100"
    assert coverage.policy_number == "POL-900"
    assert coverage.insured_identifiers[0].value == "MEM-123"
    assert coverage.plan_identifier is not None
    assert coverage.plan_identifier.identifier == "PPO"


def test_in1_parser_rejects_invalid_date_range() -> None:
    fields = _in1().split("|")
    fields[12] = "20261231"
    fields[13] = "20260101"
    with pytest.raises(InvalidMessageError, match="must not precede"):
        IN1Parser().parse_message(
            HL7Parser().parse_message(_message("|".join(fields)))
        )


def test_in1_parser_requires_set_id() -> None:
    with pytest.raises(InvalidMessageError, match="set ID is required"):
        IN1Parser().parse_message(HL7Parser().parse_message(_message("IN1||PPO")))
