from dataclasses import dataclass

from healthcare_pipeline.canonical import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical import (
    CanonicalValidationProfile,
    CanonicalValidator,
    ValidationIssue,
)


@dataclass(frozen=True, slots=True)
class BrokenRule:
    rule_id: str = "test.broken"

    def validate(
        self,
        message: CanonicalClinicalMessage,
    ) -> tuple[ValidationIssue, ...]:
        del message
        raise RuntimeError("sensitive internal detail must not escape")


def test_validator_converts_rule_failure_to_phi_safe_fatal_issue() -> None:
    profile = CanonicalValidationProfile(
        name="test",
        version="1",
        rules=(BrokenRule(),),
    )
    message = CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id="MSG-6",
        source_event_code="ADT^A01",
    )

    result = CanonicalValidator(profile).validate(message)

    assert result.is_valid is False
    assert result.errors[0].code == "VALIDATION_RULE_FAILURE"
    assert "sensitive internal detail" not in result.errors[0].message
