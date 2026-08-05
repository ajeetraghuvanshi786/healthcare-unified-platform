from __future__ import annotations

from healthcare_pipeline.parsers.detector import MessageFormatDetector
from healthcare_pipeline.parsers.registry import ParserRegistry
from healthcare_pipeline.parsers.result import ParseResult


class ParserService:
    """Coordinates detection, registry resolution, and concrete parsing."""

    def __init__(
        self,
        *,
        detector: MessageFormatDetector,
        registry: ParserRegistry,
    ) -> None:
        self._detector = detector
        self._registry = registry

    def parse(self, payload: bytes, *, correlation_id: str) -> ParseResult:
        if not isinstance(correlation_id, str):
            raise TypeError("correlation_id must be a string")
        if not correlation_id.strip():
            raise ValueError("correlation_id must not be blank")
        message_format = self._detector.detect(payload)
        parser = self._registry.resolve(message_format)
        return parser.parse(payload, correlation_id=correlation_id.strip())
