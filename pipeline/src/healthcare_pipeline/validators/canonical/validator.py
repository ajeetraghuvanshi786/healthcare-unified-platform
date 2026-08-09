from __future__ import annotations

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.profile import (
    CanonicalValidationProfile,
    default_canonical_profile,
)
from healthcare_pipeline.validators.canonical.result import CanonicalValidationResult
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


class CanonicalValidator:
    """Stateless, deterministic validator for source-neutral clinical messages."""

    def __init__(self, profile: CanonicalValidationProfile | None = None) -> None:
        self._profile = profile or default_canonical_profile()

    @property
    def profile(self) -> CanonicalValidationProfile:
        return self._profile

    def validate(self, message: CanonicalClinicalMessage) -> CanonicalValidationResult:
        if not isinstance(message, CanonicalClinicalMessage):
            raise TypeError("message must be a CanonicalClinicalMessage")

        issues: list[ValidationIssue] = []
        for rule in self._profile.rules:
            try:
                rule_issues = rule.validate(message)
            except Exception:
                issues.append(
                    ValidationIssue(
                        code="VALIDATION_RULE_FAILURE",
                        message=(
                            "A validation rule failed internally; processing must stop "
                            "until the validator configuration is corrected."
                        ),
                        severity=ValidationSeverity.FATAL,
                        path="message",
                        rule_id=rule.rule_id,
                    )
                )
                if len(issues) >= self._profile.max_issues:
                    break
                continue

            issues.extend(rule_issues)
            if len(issues) >= self._profile.max_issues:
                issues = issues[: self._profile.max_issues - 1]
                issues.append(
                    ValidationIssue(
                        code="VALIDATION_ISSUE_LIMIT_REACHED",
                        message=(
                            "Validation issue limit was reached; additional findings were "
                            "not retained."
                        ),
                        severity=ValidationSeverity.ERROR,
                        path="message",
                        rule_id="canonical.validator",
                    )
                )
                break

        return CanonicalValidationResult(
            profile_name=self._profile.name,
            profile_version=self._profile.version,
            issues=tuple(issues),
        )
