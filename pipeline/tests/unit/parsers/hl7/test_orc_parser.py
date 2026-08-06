from datetime import UTC, datetime

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, ORCParser


def test_orc_parser_maps_common_order() -> None:
    fields = [""] * 29
    fields[0] = "NW"
    fields[1] = "P100^PLACER"
    fields[2] = "F200^FILLER"
    fields[3] = "G300^GROUP"
    fields[4] = "IP"
    fields[6] = "1^Q6H"
    fields[8] = "202608061159"
    fields[9] = "111^ENTER^ERIN"
    fields[14] = "202608061200"
    fields[15] = "REASON^Clinical reason^L"
    fields[16] = "ORG^Clinic^L"
    fields[20] = "Ordering Facility"
    fields[21] = "1 MAIN ST^^BOSTON^MA^02115"
    fields[22] = "^WPN^PH^^1^617^5550100"
    fields[28] = "LAB^Laboratory^L"
    segment = "ORC|" + "|".join(fields)
    payload = (
        "MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORM^O01|1|P|2.5\r"
        + segment
    ).encode()

    order = ORCParser().parse_message(HL7Parser().parse_message(payload))[0]

    assert order.order_control == "NW"
    assert order.placer_order_number is not None
    assert order.placer_order_number.entity_identifier == "P100"
    assert order.transaction_datetime == datetime(2026, 8, 6, 11, 59, tzinfo=UTC)
    assert order.order_type is not None
    assert order.order_type.identifier == "LAB"


def test_orc_parser_requires_order_control() -> None:
    payload = b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ORM^O01|1|P|2.5\rORC||P100"

    with pytest.raises(InvalidMessageError, match="order control is required"):
        ORCParser().parse_message(HL7Parser().parse_message(payload))
