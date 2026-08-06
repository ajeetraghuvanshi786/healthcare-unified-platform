from datetime import date

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import AL1Parser, HL7Parser


def test_al1_parser_maps_repeatable_allergies() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ADT^A01|1|P|2.5\r"
        b"AL1|1|DA^Drug allergy^HL70127|7980^Penicillin^RXNORM|"
        b"SV^Severe^HL70128|RASH~HIVES|20260801\r"
        b"AL1|2|FA^Food allergy^HL70127|227493005^Cashew nuts^SCT|"
        b"MO^Moderate^HL70128|SWELLING|20260802"
    )

    allergies = AL1Parser().parse_message(HL7Parser().parse_message(payload))

    assert len(allergies) == 2
    assert allergies[0].allergen.identifier == "7980"
    assert allergies[0].reactions == ("RASH", "HIVES")
    assert allergies[0].identification_date == date(2026, 8, 1)


def test_al1_parser_rejects_missing_allergen() -> None:
    payload = b"MSH|^~\\&|APP|FAC|RCV|FAC|202608061200||ADT^A01|1|P|2.5\rAL1|1|DA"

    with pytest.raises(InvalidMessageError, match="allergen is required"):
        AL1Parser().parse_message(HL7Parser().parse_message(payload))
