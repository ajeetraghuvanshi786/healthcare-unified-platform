from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, RXAParser


def test_rxa_parser_maps_medication_administration() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||VXU^V04|1|P|2.5\r"
        b"RXA|0|1|202608061000|202608061005|207^COVID-19 vaccine^CVX|0.5|mL^milliliter^UCUM||"
        b"00^New record^NIP001|111^NURSE^NORA|CLINIC^1^A^FAC||||"
        b"LOT-1|20270101|MODERNA^Moderna^MVX|||CP|A|202608061010"
    )

    administration = RXAParser().parse_message(HL7Parser().parse_message(payload))[0]

    assert administration.administered_amount == Decimal("0.5")
    assert administration.start_datetime == datetime(2026, 8, 6, 10, 0, tzinfo=UTC)
    assert administration.expiration_date == date(2027, 1, 1)
    assert administration.lot_number == "LOT-1"


def test_rxa_parser_rejects_non_numeric_amount() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||VXU^V04|1|P|2.5\r"
        b"RXA|0|1|202608061000||207^Vaccine^CVX|abc"
    )

    with pytest.raises(InvalidMessageError, match="must be numeric"):
        RXAParser().parse_message(HL7Parser().parse_message(payload))
