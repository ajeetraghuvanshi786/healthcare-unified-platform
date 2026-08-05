from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection

from healthcare_pipeline.parsers.result import ParseResult
from healthcare_pipeline.parsers.types import MessageFormat


class BaseParser(ABC):
    """Stateless contract implemented by every concrete healthcare parser."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable parser identifier used for telemetry and audit records."""

    @property
    @abstractmethod
    def parser_version(self) -> str:
        """Version of this parser implementation."""

    @property
    @abstractmethod
    def supported_formats(self) -> Collection[MessageFormat]:
        """Message formats this parser can process."""

    @property
    def supported_message_versions(self) -> Collection[str]:
        return ()

    def supports(self, message_format: MessageFormat) -> bool:
        return message_format in self.supported_formats

    @abstractmethod
    def parse(self, payload: bytes, *, correlation_id: str) -> ParseResult:
        """Parse exact immutable payload bytes into a standardized result."""
