import pytest

from healthcare_pipeline.parsers.hl7 import HL7Delimiters


def test_default_delimiters_match_hl7_defaults() -> None:
    delimiters = HL7Delimiters.default()

    assert delimiters.field == "|"
    assert delimiters.encoding_characters == "^~\\&"


def test_extracts_delimiters_from_msh() -> None:
    delimiters = HL7Delimiters.from_msh("MSH|^~\\&|EPIC|HOSPITAL")

    assert delimiters == HL7Delimiters.default()


def test_extracts_custom_delimiters_from_msh() -> None:
    delimiters = HL7Delimiters.from_msh("MSH*$%!?*APP*FACILITY")

    assert delimiters.field == "*"
    assert delimiters.component == "$"
    assert delimiters.repetition == "%"
    assert delimiters.escape == "!"
    assert delimiters.subcomponent == "?"


def test_delimiters_are_immutable() -> None:
    delimiters = HL7Delimiters.default()

    with pytest.raises(AttributeError):
        delimiters.field = "*"  # type: ignore[misc]


@pytest.mark.parametrize(
    "msh",
    ["", "PID|1", "MSH|^~"],
)
def test_rejects_invalid_msh_prefix(msh: str) -> None:
    with pytest.raises(ValueError):
        HL7Delimiters.from_msh(msh)


def test_rejects_duplicate_delimiters() -> None:
    with pytest.raises(ValueError, match="must be unique"):
        HL7Delimiters(field="|", component="|", repetition="~", escape="\\", subcomponent="&")
