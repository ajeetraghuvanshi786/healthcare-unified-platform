from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity
from healthcare_pipeline.validators.canonical.traversal import iter_identifiers


@dataclass(frozen=True, slots=True)
class IdentifierScopeRule:
    """Detect identifiers that cannot be safely scoped across organizations/sources."""

    rule_id: str = "canonical.identifier-scope"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for path, identifier in iter_identifiers(message):
            if identifier.system is None and identifier.assigner is None:
                issues.append(
                    ValidationIssue(
                        code="IDENTIFIER_SCOPE_MISSING",
                        message=(
                            "Identifier has no system or assigner; cross-source identity "
                            "resolution may be ambiguous."
                        ),
                        severity=ValidationSeverity.WARNING,
                        path=path,
                        rule_id=self.rule_id,
                    )
                )
        return tuple(issues)
