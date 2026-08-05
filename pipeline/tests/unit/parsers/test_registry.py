from collections.abc import Collection

import pytest

from healthcare_pipeline.parsers import (
    BaseParser,
    MessageFormat,
    ParseResult,
    ParserRegistrationError,
    ParserRegistry,
    UnsupportedFormatError,
)


class StubParser(BaseParser):
    def __init__(self, formats: Collection[MessageFormat]) -> None:
        self._formats = formats

    @property
    def name(self) -> str:
        return "stub-parser"

    @property
    def parser_version(self) -> str:
        return "1.0.0"

    @property
    def supported_formats(self) -> Collection[MessageFormat]:
        return self._formats

    def parse(self, payload: bytes, *, correlation_id: str) -> ParseResult:
        return ParseResult(
            message_format=next(iter(self._formats)),
            parser_name=self.name,
            parser_version=self.parser_version,
            correlation_id=correlation_id,
            success=True,
            duration_ms=0.1,
            data=payload,
        )


def test_registry_registers_and_resolves_parser() -> None:
    registry = ParserRegistry()
    parser = StubParser((MessageFormat.JSON,))

    registry.register(parser)

    assert registry.resolve(MessageFormat.JSON) is parser
    assert registry.contains(MessageFormat.JSON)


def test_registry_registers_parser_for_multiple_formats_atomically() -> None:
    registry = ParserRegistry()
    parser = StubParser((MessageFormat.JSON, MessageFormat.FHIR_JSON))

    registry.register(parser)

    assert registry.resolve(MessageFormat.JSON) is parser
    assert registry.resolve(MessageFormat.FHIR_JSON) is parser


def test_registry_rejects_duplicate_registration() -> None:
    registry = ParserRegistry()
    registry.register(StubParser((MessageFormat.JSON,)))

    with pytest.raises(ParserRegistrationError, match="already registered"):
        registry.register(StubParser((MessageFormat.JSON, MessageFormat.XML)))

    assert not registry.contains(MessageFormat.XML)


def test_registry_rejects_parser_without_formats() -> None:
    with pytest.raises(ParserRegistrationError, match="at least one"):
        ParserRegistry().register(StubParser(()))


def test_registry_rejects_unknown_format_registration() -> None:
    with pytest.raises(ParserRegistrationError, match="UNKNOWN"):
        ParserRegistry().register(StubParser((MessageFormat.UNKNOWN,)))


def test_registry_raises_for_unsupported_format() -> None:
    with pytest.raises(UnsupportedFormatError) as exc_info:
        ParserRegistry().resolve(MessageFormat.CDA_XML)

    assert exc_info.value.message_format is MessageFormat.CDA_XML


def test_registry_unregisters_parser() -> None:
    registry = ParserRegistry()
    parser = StubParser((MessageFormat.JSON,))
    registry.register(parser)

    assert registry.unregister(MessageFormat.JSON) is parser
    assert registry.unregister(MessageFormat.JSON) is None


def test_registered_formats_are_sorted_and_immutable() -> None:
    registry = ParserRegistry()
    registry.register(StubParser((MessageFormat.XML, MessageFormat.JSON)))

    assert registry.registered_formats() == (MessageFormat.JSON, MessageFormat.XML)
