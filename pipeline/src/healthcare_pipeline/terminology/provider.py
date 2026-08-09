from __future__ import annotations

from typing import Protocol, runtime_checkable

from healthcare_pipeline.terminology.models import CodeValidationResult


@runtime_checkable
class TerminologyProvider(Protocol):
    """Provider contract for local or remote code-system validation."""

    @property
    def name(self) -> str:
        """Stable provider name used for diagnostics and cache partitioning."""
        ...

    def supports_system(self, system_uri: str) -> bool:
        """Return whether this provider can validate the canonical system URI."""
        ...

    def validate_code(
        self,
        *,
        system_uri: str,
        code: str,
        version: str | None,
    ) -> CodeValidationResult:
        """Validate one code without returning patient-specific content."""
        ...
