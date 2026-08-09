from __future__ import annotations

from dataclasses import dataclass, field

from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.terminology.cache import TerminologyValidationCache
from healthcare_pipeline.terminology.models import (
    CodeValidationResult,
    CodeValidationStatus,
    NormalizedCoding,
    TerminologyResolutionStatus,
)
from healthcare_pipeline.terminology.provider import TerminologyProvider
from healthcare_pipeline.terminology.registry import (
    DEFAULT_TERMINOLOGY_REGISTRY,
    TerminologyRegistry,
)


@dataclass(slots=True)
class TerminologyService:
    """Normalize code-system identities and validate codes through bounded providers."""

    registry: TerminologyRegistry = DEFAULT_TERMINOLOGY_REGISTRY
    providers: tuple[TerminologyProvider, ...] = ()
    cache: TerminologyValidationCache = field(default_factory=TerminologyValidationCache)

    def __post_init__(self) -> None:
        self.providers = tuple(self.providers)
        names = [provider.name for provider in self.providers]
        if len(names) != len(set(names)):
            raise ValueError("terminology provider names must be unique")

    def normalize(self, coding: Coding) -> NormalizedCoding:
        """Return a Coding whose known system identifier uses the authoritative URI."""

        if not isinstance(coding, Coding):
            raise TypeError("coding must be a Coding")
        if coding.system is None:
            return NormalizedCoding(
                coding=coding,
                status=TerminologyResolutionStatus.MISSING_SYSTEM,
            )
        system = self.registry.resolve(coding.system)
        if system is None:
            return NormalizedCoding(
                coding=coding,
                status=TerminologyResolutionStatus.UNKNOWN_SYSTEM,
            )
        if coding.system == system.canonical_uri:
            return NormalizedCoding(
                coding=coding,
                status=TerminologyResolutionStatus.ALREADY_CANONICAL,
                system=system,
            )
        normalized = Coding(
            code=coding.code,
            display=coding.display,
            system=system.canonical_uri,
            version=coding.version,
        )
        return NormalizedCoding(
            coding=normalized,
            status=TerminologyResolutionStatus.NORMALIZED,
            system=system,
        )

    def validate(self, coding: Coding) -> CodeValidationResult:
        """Validate one coded concept after authoritative system normalization."""

        normalized = self.normalize(coding)
        if normalized.coding.code is None:
            return CodeValidationResult(
                status=CodeValidationStatus.NOT_CHECKED,
                message="Text-only coding has no code to validate.",
            )
        if normalized.system is None:
            return CodeValidationResult(
                status=CodeValidationStatus.UNSUPPORTED_SYSTEM,
                message="Terminology system is missing or is not registered.",
            )
        provider = self._provider_for(normalized.system.canonical_uri)
        if provider is None:
            return CodeValidationResult(
                status=CodeValidationStatus.NOT_CHECKED,
                message="No terminology provider is configured for this system.",
            )
        code = normalized.coding.code
        cache_key = (
            normalized.system.canonical_uri,
            code,
            normalized.coding.version,
            provider.name,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = provider.validate_code(
                system_uri=normalized.system.canonical_uri,
                code=code,
                version=normalized.coding.version,
            )
        except Exception:
            return CodeValidationResult(
                status=CodeValidationStatus.PROVIDER_UNAVAILABLE,
                provider_name=provider.name,
                message="Terminology provider could not complete validation.",
            )
        self.cache.put(cache_key, result)
        return result

    def _provider_for(self, system_uri: str) -> TerminologyProvider | None:
        for provider in self.providers:
            if provider.supports_system(system_uri):
                return provider
        return None
