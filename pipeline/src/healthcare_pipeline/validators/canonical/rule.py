from __future__ import annotations

from typing import Protocol

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue


class CanonicalValidationRule(Protocol):
    """Contract implemented by deterministic canonical validation rules."""

    @property
    def rule_id(self) -> str:
        """Stable identifier used for auditability and rule-level reporting."""
        ...

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]: ...
