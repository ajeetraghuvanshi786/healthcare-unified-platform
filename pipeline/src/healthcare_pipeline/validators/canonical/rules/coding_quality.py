from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity
from healthcare_pipeline.validators.canonical.traversal import iter_codings


@dataclass(frozen=True, slots=True)
class CodingSystemRule:
    """Identify coded values that cannot yet be resolved against a terminology system."""

    rule_id: str = "canonical.coding-system"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for path, coding in iter_codings(message):
            if coding.code is not None and coding.system is None:
                issues.append(
                    ValidationIssue(
                        code="CODING_SYSTEM_MISSING",
                        message=(
                            "Coded concept contains a code without a coding system; "
                            "terminology normalization may be ambiguous."
                        ),
                        severity=ValidationSeverity.WARNING,
                        path=path,
                        rule_id=self.rule_id,
                    )
                )
            elif coding.code is None and coding.display is not None:
                issues.append(
                    ValidationIssue(
                        code="CODING_TEXT_ONLY",
                        message=(
                            "Concept contains display text without a code; automated "
                            "terminology matching will require later normalization."
                        ),
                        severity=ValidationSeverity.INFO,
                        path=path,
                        rule_id=self.rule_id,
                    )
                )
        return tuple(issues)
