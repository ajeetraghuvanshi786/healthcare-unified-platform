import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, RXRParser


def test_rxr_parser_maps_route_details() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||RDE^O11|1|P|2.5\r"
        b"RXR|PO^Oral^HL70162|MOUTH^Mouth^L|SYR^Syringe^L|"
        b"SWALLOW^Swallow^L|WITH FOOD^With food^L|LEFT^Left^L"
    )

    route = RXRParser().parse_message(HL7Parser().parse_message(payload))[0]

    assert route.route.identifier == "PO"
    assert route.administration_method is not None
    assert route.administration_method.identifier == "SWALLOW"


def test_rxr_parser_requires_route() -> None:
    payload = b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||RDE^O11|1|P|2.5\rRXR|"

    with pytest.raises(InvalidMessageError, match="route is required"):
        RXRParser().parse_message(HL7Parser().parse_message(payload))
