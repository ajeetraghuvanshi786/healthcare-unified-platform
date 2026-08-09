import pytest

from healthcare_pipeline.validators.canonical import (
    CanonicalValidationProfile,
    CanonicalValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from healthcare_pipeline.validators.canonical.rules import PatientContextRule


def test_validation_issue_normalizes_and_blocks_for_error() -> None:
    issue = ValidationIssue(
        code=" patient_context_required ",
        message=" Patient context is required. ",
        severity=ValidationSeverity.ERROR,
        path=" patient ",
        rule_id=" canonical.patient-context ",
    )

    assert issue.code == "PATIENT_CONTEXT_REQUIRED"
    assert issue.blocks_processing is True


def test_validation_result_partitions_findings() -> None:
    warning = ValidationIssue(
        code="WARNING",
        message="warning",
        severity=ValidationSeverity.WARNING,
        path="message",
        rule_id="test.warning",
    )
    error = ValidationIssue(
        code="ERROR",
        message="error",
        severity=ValidationSeverity.ERROR,
        path="message",
        rule_id="test.error",
    )

    result = CanonicalValidationResult("baseline", "1", (warning, error))

    assert result.is_valid is False
    assert result.warnings == (warning,)
    assert result.errors == (error,)


def test_profile_rejects_duplicate_rule_ids() -> None:
    with pytest.raises(ValueError, match="duplicate rule_id"):
        CanonicalValidationProfile(
            name="duplicate",
            version="1",
            rules=(PatientContextRule(), PatientContextRule()),
        )
