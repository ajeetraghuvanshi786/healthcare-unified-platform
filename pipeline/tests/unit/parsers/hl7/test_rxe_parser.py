from decimal import Decimal

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, RXEParser


def test_rxe_parser_maps_pharmacy_order() -> None:
    fields = [""] * 31
    fields[0] = "1^BID"
    fields[1] = "860975^Metformin 500 MG tablet^RXNORM"
    fields[2] = "1"
    fields[3] = "2"
    fields[4] = "TAB^tablet^L"
    fields[5] = "TAB^tablet^L"
    fields[6] = "TAKE^Take with food^L"
    fields[9] = "60"
    fields[10] = "TAB^tablet^L"
    fields[11] = "2"
    fields[12] = "111^SMITH^JANE"
    fields[22] = "2"
    fields[23] = "TAB/H^tablets per hour^UCUM"
    fields[24] = "500"
    fields[25] = "mg^milligram^UCUM"
    fields[30] = "SUP^Supplemental^L"
    segment = "RXE|" + "|".join(fields)
    payload = (
        "MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||RDE^O11|1|P|2.5\r" + segment
    ).encode()

    order = RXEParser().parse_message(HL7Parser().parse_message(payload))[0]

    assert order.give_code.identifier == "860975"
    assert order.give_amount_minimum == Decimal("1")
    assert order.dispense_amount == Decimal("60")
    assert order.number_of_refills == 2
    assert order.give_strength == Decimal("500")


def test_rxe_parser_requires_give_code() -> None:
    payload = b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||RDE^O11|1|P|2.5\rRXE|1^BID|"

    with pytest.raises(InvalidMessageError, match="give code is required"):
        RXEParser().parse_message(HL7Parser().parse_message(payload))
