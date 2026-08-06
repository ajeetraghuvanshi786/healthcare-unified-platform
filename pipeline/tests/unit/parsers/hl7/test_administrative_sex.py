import pytest

from healthcare_pipeline.parsers.hl7 import AdministrativeSex


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("M", AdministrativeSex.MALE),
        ("f", AdministrativeSex.FEMALE),
        (" O ", AdministrativeSex.OTHER),
        ("A", AdministrativeSex.AMBIGUOUS),
        ("N", AdministrativeSex.NOT_APPLICABLE),
        ("U", AdministrativeSex.UNKNOWN),
        ("", AdministrativeSex.UNKNOWN),
        (None, AdministrativeSex.UNKNOWN),
    ],
)
def test_administrative_sex_parses_hl7_codes(
    code: str | None,
    expected: AdministrativeSex,
) -> None:
    assert AdministrativeSex.from_code(code) is expected


def test_administrative_sex_rejects_unknown_code() -> None:
    with pytest.raises(ValueError, match="unsupported HL7"):
        AdministrativeSex.from_code("X")


def test_administrative_sex_rejects_non_string() -> None:
    with pytest.raises(TypeError, match="string or None"):
        AdministrativeSex.from_code(1)  # type: ignore[arg-type]
