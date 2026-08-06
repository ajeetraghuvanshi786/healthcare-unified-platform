from __future__ import annotations

from datetime import date

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import (
    AdministrativeSex,
    HL7Parser,
    PIDParser,
)


def _parse(payload: bytes):
    return PIDParser().parse_message(HL7Parser().parse_message(payload))


def test_pid_parser_maps_complete_patient_demographics() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|HIE|NETWORK|202608061030||ADT^A01|MSG-1|P|2.5.1\r"
        b"PID|1||123456^7^M10^GENERAL_HOSPITAL^MR^MAIN_FACILITY~"
        b"UHC998877^^^UHC^MB||DOE&ORIGINAL^JOHN^MICHAEL^JR^MR^PHD^L~"
        b"SMITH^JOHNNY^^^^^N||199001151230|M|||"
        b"123 MAIN ST^APT 4^BOSTON^MA^02115^USA^H^^SUFFOLK^001200~"
        b"PO BOX 9^^CAMBRIDGE^MA^02139^USA^M||"
        b"+1-617-555-0100^PRN^PH^^1^617^5550100^22~"
        b"^NET^Internet^john@example.org|"
        b"^WPN^PH^^1^508^5550199^7||||"
        b"ACCT-99^^^GENERAL_HOSPITAL^AN"
    )

    patient = _parse(payload)

    assert patient.set_id == 1
    assert len(patient.identifiers) == 2
    assert patient.identifiers[0].value == "123456"
    assert patient.identifiers[0].check_digit == "7"
    assert patient.identifiers[0].check_digit_scheme == "M10"
    assert patient.identifiers[0].assigning_authority == "GENERAL_HOSPITAL"
    assert patient.identifiers[0].identifier_type == "MR"
    assert patient.identifiers[0].assigning_facility == "MAIN_FACILITY"
    assert patient.identifiers[1].value == "UHC998877"

    assert len(patient.names) == 2
    assert patient.names[0].family_name == "DOE"
    assert patient.names[0].given_name == "JOHN"
    assert patient.names[0].middle_name == "MICHAEL"
    assert patient.names[0].suffix == "JR"
    assert patient.names[0].prefix == "MR"
    assert patient.names[0].degree == "PHD"
    assert patient.names[0].name_type == "L"
    assert patient.names[1].family_name == "SMITH"

    assert patient.birth_date == date(1990, 1, 15)
    assert patient.administrative_sex is AdministrativeSex.MALE

    assert len(patient.addresses) == 2
    assert patient.addresses[0].street_address == "123 MAIN ST"
    assert patient.addresses[0].city == "BOSTON"
    assert patient.addresses[0].county == "SUFFOLK"
    assert patient.addresses[0].census_tract == "001200"

    assert len(patient.phones) == 3
    assert patient.phones[0].number == "+1-617-555-0100"
    assert patient.phones[0].extension == "22"
    assert patient.phones[1].email == "john@example.org"
    assert patient.phones[2].use_code == "WPN"

    assert patient.patient_account_number is not None
    assert patient.patient_account_number.value == "ACCT-99"
    assert patient.patient_account_number.identifier_type == "AN"


def test_pid_parser_supports_selected_pid_occurrence() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-2|P|2.5\r"
        b"PID|1||FIRST^^^FAC^MR||ONE^PATIENT\r"
        b"PID|2||SECOND^^^FAC^MR||TWO^PATIENT"
    )
    message = HL7Parser().parse_message(payload)

    patient = PIDParser().parse_message(message, occurrence=2)

    assert patient.set_id == 2
    assert patient.primary_identifier.value == "SECOND"
    assert patient.official_name.family_name == "TWO"


def test_pid_parser_defaults_optional_demographics() -> None:
    patient = _parse(
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-3|P|2.5\r"
        b"PID|1||123^^^FAC^MR||DOE^JANE"
    )

    assert patient.birth_date is None
    assert patient.administrative_sex is AdministrativeSex.UNKNOWN
    assert patient.addresses == ()
    assert patient.phones == ()
    assert patient.patient_account_number is None


def test_pid_parser_rejects_missing_pid_segment() -> None:
    message = HL7Parser().parse_message(
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-4|P|2.5"
    )

    with pytest.raises(InvalidMessageError, match="PID segment occurrence 1 is missing"):
        PIDParser().parse_message(message)


def test_pid_parser_rejects_non_pid_segment() -> None:
    message = HL7Parser().parse_message(
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-5|P|2.5\r"
        b"PV1|1|I"
    )

    with pytest.raises(InvalidMessageError, match="requires a PID segment"):
        PIDParser().parse_segment(message.segment("PV1"))


@pytest.mark.parametrize(
    ("pid", "expected_message"),
    [
        (b"PID|ABC||123^^^FAC^MR||DOE^JANE", "set ID must be an integer"),
        (b"PID|0||123^^^FAC^MR||DOE^JANE", "set_id must be greater than zero"),
        (b"PID|1||||DOE^JANE", "at least one identifier"),
        (b"PID|1||123^^^FAC^MR", "at least one name"),
        (
            b"PID|1||123^^^FAC^MR||DOE^JANE||20261301",
            "not a valid calendar date",
        ),
        (
            b"PID|1||123^^^FAC^MR||DOE^JANE||19900115|X",
            "unsupported HL7 administrative sex code",
        ),
        (
            b"PID|1||123^^^FAC^MR~123^^^FAC^MR||DOE^JANE",
            "must not contain duplicates",
        ),
    ],
)
def test_pid_parser_rejects_invalid_pid_values(
    pid: bytes,
    expected_message: str,
) -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-6|P|2.5\r"
        + pid
    )

    with pytest.raises(InvalidMessageError, match=expected_message):
        _parse(payload)


def test_pid_parser_rejects_identifier_without_value() -> None:
    payload = (
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-7|P|2.5\r"
        b"PID|1||^^^FAC^MR||DOE^JANE"
    )

    with pytest.raises(InvalidMessageError, match="required component 1"):
        _parse(payload)


def test_pid_parser_validates_argument_types_and_occurrence() -> None:
    parser = PIDParser()

    with pytest.raises(TypeError, match="message must be an HL7Message"):
        parser.parse_message("not-a-message")  # type: ignore[arg-type]

    message = HL7Parser().parse_message(
        b"MSH|^~\\&|APP|FAC|APP2|FAC2|202608061030||ADT^A01|MSG-8|P|2.5\r"
        b"PID|1||123^^^FAC^MR||DOE^JANE"
    )

    with pytest.raises(TypeError, match="occurrence must be an integer"):
        parser.parse_message(message, occurrence="1")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="greater than zero"):
        parser.parse_message(message, occurrence=0)
