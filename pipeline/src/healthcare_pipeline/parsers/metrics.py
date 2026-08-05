from __future__ import annotations

from typing import Protocol

from healthcare_pipeline.parsers.types import MessageFormat


class ParserMetrics(Protocol):
    def record_detection(self, message_format: MessageFormat) -> None: ...

    def record_parse(
        self,
        *,
        message_format: MessageFormat,
        parser_name: str,
        success: bool,
        duration_ms: float,
    ) -> None: ...


class NoOpParserMetrics:
    """Default metrics adapter used until a telemetry backend is configured."""

    def record_detection(self, message_format: MessageFormat) -> None:
        del message_format

    def record_parse(
        self,
        *,
        message_format: MessageFormat,
        parser_name: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        del message_format, parser_name, success, duration_ms
