from __future__ import annotations

from collections.abc import Collection
from time import perf_counter

from healthcare_pipeline.parsers.base import BaseParser
from healthcare_pipeline.parsers.exceptions import (
    InvalidMessageError,
    InvalidPayloadError,
)
from healthcare_pipeline.parsers.hl7.builder import HL7MessageBuilder
from healthcare_pipeline.parsers.hl7.decoder import HL7PayloadDecoder
from healthcare_pipeline.parsers.hl7.message import HL7Message
from healthcare_pipeline.parsers.hl7.normalizer import HL7MessageNormalizer
from healthcare_pipeline.parsers.result import ParseIssue, ParseResult
from healthcare_pipeline.parsers.types import MessageFormat


class HL7Parser(BaseParser):
    """Stateless structural parser for HL7 v2 payloads."""

    def __init__(
        self,
        *,
        decoder: HL7PayloadDecoder | None = None,
        normalizer: HL7MessageNormalizer | None = None,
        builder: HL7MessageBuilder | None = None,
    ) -> None:
        self._decoder = decoder or HL7PayloadDecoder()
        self._normalizer = normalizer or HL7MessageNormalizer()
        self._builder = builder or HL7MessageBuilder()

    @property
    def name(self) -> str:
        return "hl7-v2-structural-parser"

    @property
    def parser_version(self) -> str:
        return "1.0.0"

    @property
    def supported_formats(self) -> Collection[MessageFormat]:
        return (MessageFormat.HL7_V2,)

    def parse_message(self, payload: bytes) -> HL7Message:
        """Parse bytes into an immutable HL7 message or raise a typed error."""

        decoded_message = self._decoder.decode(payload)
        normalized_message = self._normalizer.normalize(decoded_message)
        self._normalizer.split_segments(normalized_message)
        return self._builder.build_message(
            raw_value=decoded_message,
            normalized_value=normalized_message,
        )

    def parse(self, payload: bytes, *, correlation_id: str) -> ParseResult:
        """Parse HL7 bytes into the parser framework's standardized result."""

        if not isinstance(correlation_id, str):
            raise TypeError("correlation_id must be a string")
        normalized_correlation_id = correlation_id.strip()
        if not normalized_correlation_id:
            raise ValueError("correlation_id must not be blank")

        started_at = perf_counter()
        try:
            message = self.parse_message(payload)
        except (InvalidPayloadError, InvalidMessageError) as exc:
            duration_ms = (perf_counter() - started_at) * 1000
            return ParseResult(
                message_format=MessageFormat.HL7_V2,
                parser_name=self.name,
                parser_version=self.parser_version,
                correlation_id=normalized_correlation_id,
                success=False,
                duration_ms=duration_ms,
                errors=(
                    ParseIssue(
                        code="HL7_STRUCTURE_INVALID",
                        message=str(exc),
                    ),
                ),
                metadata={"encoding": "utf-8"},
            )

        duration_ms = (perf_counter() - started_at) * 1000
        return ParseResult(
            message_format=MessageFormat.HL7_V2,
            parser_name=self.name,
            parser_version=self.parser_version,
            correlation_id=normalized_correlation_id,
            success=True,
            duration_ms=duration_ms,
            data=message,
            metadata={
                "encoding": "utf-8",
                "segment_count": len(message.segments),
                "field_separator": message.delimiters.field,
            },
        )
