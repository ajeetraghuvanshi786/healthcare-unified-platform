from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.delimiters import HL7Delimiters
from healthcare_pipeline.parsers.hl7.segment import HL7Segment


@dataclass(frozen=True, slots=True)
class HL7Message:
    """Immutable structural representation of a complete HL7 v2 message."""

    raw_value: str
    delimiters: HL7Delimiters
    segments: tuple[HL7Segment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raw_value, str) or not self.raw_value:
            raise ValueError("raw_value must be a non-empty string")
        if not isinstance(self.delimiters, HL7Delimiters):
            raise TypeError("delimiters must be an HL7Delimiters instance")
        if not self.segments:
            raise ValueError("HL7 message must contain at least one segment")
        if not all(isinstance(value, HL7Segment) for value in self.segments):
            raise TypeError("all segments must be HL7Segment instances")
        if self.segments[0].name != "MSH":
            raise ValueError("first HL7 segment must be MSH")
        object.__setattr__(self, "segments", tuple(self.segments))

    def segment(self, name: str, *, occurrence: int = 1) -> HL7Segment:
        if occurrence < 1:
            raise IndexError("segment occurrence must be one or greater")
        normalized_name = name.strip().upper()
        matches = tuple(segment for segment in self.segments if segment.name == normalized_name)
        try:
            return matches[occurrence - 1]
        except IndexError as exc:
            raise IndexError(
                f"segment {normalized_name!r} occurrence {occurrence} does not exist"
            ) from exc

    def segments_named(self, name: str) -> tuple[HL7Segment, ...]:
        normalized_name = name.strip().upper()
        return tuple(segment for segment in self.segments if segment.name == normalized_name)
