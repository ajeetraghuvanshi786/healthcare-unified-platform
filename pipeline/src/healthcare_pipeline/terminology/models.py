from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from healthcare_pipeline.canonical.common.coding import Coding


class TerminologyResolutionStatus(StrEnum):
    """Outcome of resolving an incoming code-system identifier."""

    ALREADY_CANONICAL = "already_canonical"
    NORMALIZED = "normalized"
    MISSING_SYSTEM = "missing_system"
    UNKNOWN_SYSTEM = "unknown_system"


class CodeValidationStatus(StrEnum):
    """Outcome of terminology-code validation."""

    VALID = "valid"
    INVALID = "invalid"
    NOT_CHECKED = "not_checked"
    UNSUPPORTED_SYSTEM = "unsupported_system"
    PROVIDER_UNAVAILABLE = "provider_unavailable"


@dataclass(frozen=True, slots=True)
class TerminologySystem:
    """Authoritative identity and accepted local aliases for a code system."""

    name: str
    canonical_uri: str
    aliases: tuple[str, ...] = ()
    oid: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        canonical_uri = self.canonical_uri.strip()
        if not name:
            raise ValueError("name must not be blank")
        if not canonical_uri:
            raise ValueError("canonical_uri must not be blank")
        aliases = tuple(alias.strip() for alias in self.aliases if alias.strip())
        if len(aliases) != len(set(aliases)):
            raise ValueError("aliases must not contain exact duplicates")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "canonical_uri", canonical_uri)
        object.__setattr__(self, "aliases", aliases)
        if self.oid is not None:
            oid = self.oid.strip()
            object.__setattr__(self, "oid", oid or None)


@dataclass(frozen=True, slots=True)
class NormalizedCoding:
    """A Coding plus resolution metadata without mutating the source object."""

    coding: Coding
    status: TerminologyResolutionStatus
    system: TerminologySystem | None = None


@dataclass(frozen=True, slots=True)
class CodeValidationResult:
    """PHI-safe code-validation result returned by terminology providers."""

    status: CodeValidationStatus
    provider_name: str | None = None
    message: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.status is CodeValidationStatus.VALID


@dataclass(frozen=True, slots=True)
class CodingAssessment:
    """Terminology assessment associated with a structural canonical path."""

    path: str
    normalized: NormalizedCoding
    validation: CodeValidationResult
