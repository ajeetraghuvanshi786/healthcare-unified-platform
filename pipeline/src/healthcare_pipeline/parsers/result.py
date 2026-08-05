from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from healthcare_pipeline.parsers.types import MessageFormat, MetadataValue, ParsedData


@dataclass(frozen=True, slots=True)
class ParseIssue:
    code: str
    message: str
    path: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("issue code must not be blank")
        if not self.message.strip():
            raise ValueError("issue message must not be blank")


@dataclass(frozen=True, slots=True)
class ParseResult:
    message_format: MessageFormat
    parser_name: str
    parser_version: str
    correlation_id: str
    success: bool
    duration_ms: float
    data: ParsedData | None = None
    warnings: tuple[ParseIssue, ...] = ()
    errors: tuple[ParseIssue, ...] = ()
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.parser_name.strip():
            raise ValueError("parser_name must not be blank")
        if not self.parser_version.strip():
            raise ValueError("parser_version must not be blank")
        if not self.correlation_id.strip():
            raise ValueError("correlation_id must not be blank")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must not be negative")
        if self.success and self.errors:
            raise ValueError("successful parse results must not contain errors")
        if not self.success and not self.errors:
            raise ValueError("failed parse results must contain at least one error")

        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
