from __future__ import annotations

from healthcare_pipeline.parsers.types import MessageFormat


class ParserError(Exception):
    """Base exception for parser-framework failures."""


class InvalidPayloadError(ParserError):
    """Raised when a parser or detector receives an unusable payload."""


class UnsupportedFormatError(ParserError):
    """Raised when no parser is available for a message format."""

    def __init__(self, message_format: MessageFormat) -> None:
        self.message_format = message_format
        super().__init__(
            f"no parser is registered for message format: {message_format.value}"
        )


class ParserRegistrationError(ParserError):
    """Raised when parser registration would make the registry ambiguous."""


class InvalidMessageError(ParserError):
    """Raised when a supported message is structurally invalid."""


class VersionMismatchError(ParserError):
    """Raised when a message version is unsupported by a parser."""
