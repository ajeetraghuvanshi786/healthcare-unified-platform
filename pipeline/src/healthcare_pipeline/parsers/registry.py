from __future__ import annotations

from threading import RLock

from healthcare_pipeline.parsers.base import BaseParser
from healthcare_pipeline.parsers.exceptions import (
    ParserRegistrationError,
    UnsupportedFormatError,
)
from healthcare_pipeline.parsers.types import MessageFormat


class ParserRegistry:
    """Thread-safe registry that resolves one parser per message format."""

    def __init__(self) -> None:
        self._parsers: dict[MessageFormat, BaseParser] = {}
        self._lock = RLock()

    def register(self, parser: BaseParser) -> None:
        formats = tuple(parser.supported_formats)
        if not formats:
            raise ParserRegistrationError(
                f"parser {parser.name!r} must support at least one format"
            )
        if MessageFormat.UNKNOWN in formats:
            raise ParserRegistrationError("UNKNOWN cannot be registered")
        if len(set(formats)) != len(formats):
            raise ParserRegistrationError(
                f"parser {parser.name!r} declares duplicate formats"
            )

        with self._lock:
            conflicts = [item for item in formats if item in self._parsers]
            if conflicts:
                values = ", ".join(item.value for item in conflicts)
                raise ParserRegistrationError(
                    f"message formats already registered: {values}"
                )
            for message_format in formats:
                self._parsers[message_format] = parser

    def unregister(self, message_format: MessageFormat) -> BaseParser | None:
        with self._lock:
            return self._parsers.pop(message_format, None)

    def resolve(self, message_format: MessageFormat) -> BaseParser:
        with self._lock:
            parser = self._parsers.get(message_format)
        if parser is None:
            raise UnsupportedFormatError(message_format)
        return parser

    def contains(self, message_format: MessageFormat) -> bool:
        with self._lock:
            return message_format in self._parsers

    def registered_formats(self) -> tuple[MessageFormat, ...]:
        with self._lock:
            return tuple(sorted(self._parsers, key=lambda item: item.value))
