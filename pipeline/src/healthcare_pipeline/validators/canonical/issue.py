from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_required
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """PHI-safe validation finding for a canonical resource or message."""

    code: str
    message: str
    severity: ValidationSeverity
    path: str
    rule_id: str

    def __post_init__(self) -> None:
        for field_name in ("code", "message", "path", "rule_id"):
            object.__setattr__(
                self,
                field_name,
                normalize_required(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "code", self.code.upper())
        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("severity must be a ValidationSeverity")

    @property
    def blocks_processing(self) -> bool:
        return self.severity.blocks_processing
