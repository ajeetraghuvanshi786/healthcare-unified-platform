import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7Parser, NK1Parser


def _message(nk1_segments: str) -> bytes:
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        "PID|1||123^^^HOSPITAL^MR||DOE^JOHN\r"
        f"{nk1_segments}"
    ).encode()


def test_nk1_parser_maps_multiple_contacts() -> None:
    payload = _message(
        "NK1|1|DOE^JANE|SPO^Spouse^HL70063|1 MAIN ST^^BOSTON^MA^02110|"
        "5551112222^PRN^PH||||||||||||F|19820101\r"
        "NK1|2|DOE^ROBERT|FTH^Father^HL70063||||||||||||||M|19500101"
    )

    contacts = NK1Parser().parse_message(HL7Parser().parse_message(payload))

    assert len(contacts) == 2
    assert contacts[0].primary_name.given_name == "JANE"
    assert contacts[0].relationship is not None
    assert contacts[0].relationship.identifier == "SPO"
    assert contacts[0].phones[0].number == "5551112222"
    assert contacts[1].primary_name.given_name == "ROBERT"


def test_nk1_parser_returns_empty_tuple_when_absent() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|HIE|HOSPITAL|202608061200||ADT^A01|M1|P|2.5\r"
        b"PID|1||123^^^HOSPITAL^MR||DOE^JOHN"
    )
    assert NK1Parser().parse_message(HL7Parser().parse_message(payload)) == ()


def test_nk1_parser_rejects_missing_name() -> None:
    with pytest.raises(InvalidMessageError, match="at least one name"):
        NK1Parser().parse_message(HL7Parser().parse_message(_message("NK1|1||SPO")))
