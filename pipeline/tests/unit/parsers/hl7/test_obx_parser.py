from datetime import UTC, datetime

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, OBXParser


def test_obx_parser_maps_multiple_results() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORU^R01|1|P|2.5\r"
        b"OBX|1|NM|718-7^Hemoglobin^LN||13.4|g/dL^grams per deciliter^UCUM|"
        b"12-16|N|||F|||202608061100|LAB^Lab^L|111^SMITH^JANE|"
        b"AUTO^Automated^L|EQ-1|202608061130\r"
        b"OBX|2|ST|NOTE^Comment^L||Specimen acceptable||||||F"
    )

    results = OBXParser().parse_message(HL7Parser().parse_message(payload))

    assert len(results) == 2
    assert results[0].values == ("13.4",)
    assert results[0].abnormal_flags == ("N",)
    assert results[0].analysis_datetime == datetime(2026, 8, 6, 11, 30, tzinfo=UTC)
    assert results[1].values == ("Specimen acceptable",)


def test_obx_parser_requires_result_value() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORU^R01|1|P|2.5\r"
        b"OBX|1|NM|718-7^Hemoglobin^LN||||||||F"
    )

    with pytest.raises(InvalidMessageError, match="values must contain"):
        OBXParser().parse_message(HL7Parser().parse_message(payload))
