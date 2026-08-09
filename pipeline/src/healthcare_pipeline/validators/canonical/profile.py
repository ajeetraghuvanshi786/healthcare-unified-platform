from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_required
from healthcare_pipeline.validators.canonical.rule import CanonicalValidationRule
from healthcare_pipeline.validators.canonical.rules import (
    CodingSystemRule,
    CoverageIdentityRule,
    EncounterContextRule,
    EncounterTemporalRule,
    IdentifierScopeRule,
    MedicationDoseRule,
    ObservationQualityRule,
    PatientContextRule,
)


@dataclass(frozen=True, slots=True)
class CanonicalValidationProfile:
    """Versioned set of source-neutral data-quality and safety rules."""

    name: str
    version: str
    rules: tuple[CanonicalValidationRule, ...]
    max_issues: int = 1000

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_required(self.name, "name"))
        object.__setattr__(self, "version", normalize_required(self.version, "version"))
        rules = tuple(self.rules)
        if not rules:
            raise ValueError("rules must contain at least one validation rule")
        rule_ids = [rule.rule_id for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rules must not contain duplicate rule_id values")
        if self.max_issues < 1:
            raise ValueError("max_issues must be greater than zero")
        object.__setattr__(self, "rules", rules)


def default_canonical_profile() -> CanonicalValidationProfile:
    """Return the production baseline profile for canonical clinical messages."""

    rules: tuple[CanonicalValidationRule, ...] = (
        PatientContextRule(),
        EncounterContextRule(),
        IdentifierScopeRule(),
        CodingSystemRule(),
        EncounterTemporalRule(),
        ObservationQualityRule(),
        MedicationDoseRule(),
        CoverageIdentityRule(),
    )
    return CanonicalValidationProfile(
        name="canonical-clinical-baseline",
        version="1.0.0",
        rules=rules,
    )
