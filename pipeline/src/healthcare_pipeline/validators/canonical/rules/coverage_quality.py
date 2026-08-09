from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class CoverageIdentityRule:
    """Ensure payer coverage contains enough identity data for downstream matching."""

    rule_id: str = "canonical.coverage-identity"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for index, coverage in enumerate(message.coverages):
            has_payer = bool(coverage.payer_identifiers) or coverage.payer_name is not None
            has_policy = bool(coverage.policy_identifiers)
            has_subscriber = bool(coverage.subscriber_identifiers)
            if not any((has_payer, has_policy, has_subscriber)):
                issues.append(
                    ValidationIssue(
                        code="COVERAGE_IDENTITY_INCOMPLETE",
                        message=(
                            "Coverage has no payer, policy, or subscriber identifier; "
                            "matching and adjudication workflows may be unreliable."
                        ),
                        severity=ValidationSeverity.WARNING,
                        path=f"coverages[{index}]",
                        rule_id=self.rule_id,
                    )
                )
        return tuple(issues)
