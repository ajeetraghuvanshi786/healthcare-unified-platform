from datetime import date

from healthcare_pipeline.canonical import (
    Address,
    ContactPoint,
    ContactPointSystem,
    HumanName,
    Identifier,
    Patient,
)
from healthcare_pipeline.identity import PatientIdentityNormalizer


def test_normalizer_builds_conservative_identity_features() -> None:
    patient = Patient(
        identifiers=(Identifier("MRN-001", system="HOSP-A", type_code="MR"),),
        names=(HumanName(family="Doe", given=("Jane",)),),
        birth_date=date(1990, 1, 2),
        addresses=(Address(postal_code="02747"),),
        telecom=(
            ContactPoint(ContactPointSystem.PHONE, "(508) 555-1212"),
            ContactPoint(ContactPointSystem.EMAIL, "Jane@example.com"),
        ),
    )

    normalized = PatientIdentityNormalizer().normalize(patient)

    assert normalized.scoped_identifiers == ("HOSP-A\x1fMR\x1fMRN-001",)
    assert normalized.name_keys == ("jane doe",)
    assert normalized.birth_date == "1990-01-02"
    assert normalized.phones == ("5085551212",)
    assert normalized.emails == ("jane@example.com",)
    assert normalized.postal_codes == ("02747",)


def test_unscoped_identifier_is_not_a_strong_identity_key() -> None:
    assert PatientIdentityNormalizer.identifier_key(Identifier("123")) is None
