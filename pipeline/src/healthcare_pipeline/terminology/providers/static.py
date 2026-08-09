from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from healthcare_pipeline.terminology.models import CodeValidationResult, CodeValidationStatus


@dataclass(frozen=True, slots=True)
class StaticTerminologyProvider:
    """Exact local code-set provider suitable for curated/offline terminology subsets."""

    name: str
    code_sets: Mapping[str, frozenset[str]]

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("name must not be blank")
        normalized: dict[str, frozenset[str]] = {}
        for system_uri, codes in self.code_sets.items():
            uri = system_uri.strip()
            if not uri:
                raise ValueError("code-set system URI must not be blank")
            normalized[uri] = frozenset(codes)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "code_sets", MappingProxyType(normalized))

    def supports_system(self, system_uri: str) -> bool:
        return system_uri in self.code_sets

    def validate_code(
        self,
        *,
        system_uri: str,
        code: str,
        version: str | None,
    ) -> CodeValidationResult:
        del version
        codes = self.code_sets.get(system_uri)
        if codes is None:
            return CodeValidationResult(
                status=CodeValidationStatus.UNSUPPORTED_SYSTEM,
                provider_name=self.name,
                message="Provider does not support this terminology system.",
            )
        if code in codes:
            return CodeValidationResult(
                status=CodeValidationStatus.VALID,
                provider_name=self.name,
                message="Code is present in the configured terminology set.",
            )
        return CodeValidationResult(
            status=CodeValidationStatus.INVALID,
            provider_name=self.name,
            message="Code is not present in the configured terminology set.",
        )
