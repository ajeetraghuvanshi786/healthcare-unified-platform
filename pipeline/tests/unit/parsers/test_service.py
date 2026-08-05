from collections.abc import Collection

import pytest

from healthcare_pipeline.parsers import (
    BaseParser,
    MessageFormat,
    MessageFormatDetector,
    ParseResult,
    ParserRegistry,
    ParserService,
    UnsupportedFormatError,
)


class JsonParser(BaseParser):
    @property
    def name(self) -> str:
        return "json-parser"

    @property
    def parser_version(self) -> str:
        return "1.0.0"

    @property
    def supported_formats(self) -> Collection[MessageFormat]:
        return (MessageFormat.JSON,)

    def parse(self, payload: bytes, *, correlation_id: str) -> ParseResult:
        return ParseResult(
            message_format=MessageFormat.JSON,
            parser_name=self.name,
            parser_version=self.parser_version,
            correlation_id=correlation_id,
            success=True,
            duration_ms=0.2,
            data=payload.decode("utf-8"),
        )


def build_service() -> ParserService:
    registry = ParserRegistry()
    registry.register(JsonParser())
    return ParserService(detector=MessageFormatDetector(), registry=registry)


def test_service_detects_resolves_and_parses() -> None:
    result = build_service().parse(b'{"patient":"1"}', correlation_id=" corr-1 ")

    assert result.success
    assert result.message_format is MessageFormat.JSON
    assert result.correlation_id == "corr-1"


def test_service_rejects_blank_correlation_id() -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        build_service().parse(b'{"patient":"1"}', correlation_id=" ")


def test_service_rejects_non_string_correlation_id() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        build_service().parse(
            b'{"patient":"1"}', correlation_id=123  # type: ignore[arg-type]
        )


def test_service_raises_when_detected_format_is_unregistered() -> None:
    with pytest.raises(UnsupportedFormatError):
        build_service().parse(
            b'{"resourceType":"Patient"}', correlation_id="corr-1"
        )
