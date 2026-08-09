from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_required
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class CanonicalValidationResult:
    """Immutable result produced by canonical message validation."""

    profile_name: str
    profile_version: str
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "profile_name",
            normalize_required(self.profile_name, "profile_name"),
        )
        object.__setattr__(
            self,
            "profile_version",
            normalize_required(self.profile_version, "profile_version"),
        )
        issues = tuple(self.issues)
        if not all(isinstance(issue, ValidationIssue) for issue in issues):
            raise TypeError("issues must contain ValidationIssue values")
        object.__setattr__(self, "issues", issues)

    @property
    def is_valid(self) -> bool:
        return not any(issue.blocks_processing for issue in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity in {ValidationSeverity.ERROR, ValidationSeverity.FATAL}
        )

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity is ValidationSeverity.WARNING
        )

    @property
    def infos(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is ValidationSeverity.INFO)
