from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.field import HL7Field


@dataclass(frozen=True, slots=True)
class HL7Segment:
    """Immutable structural representation of one HL7 segment."""

    name: str
    raw_value: str
    fields: tuple[HL7Field, ...]
    sequence: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or len(self.name) != 3:
            raise ValueError("HL7 segment name must contain exactly three characters")
        if not self.name.isalnum() or self.name != self.name.upper():
            raise ValueError("HL7 segment name must be uppercase alphanumeric")
        if not isinstance(self.raw_value, str):
            raise TypeError("raw_value must be a string")
        if self.sequence < 1:
            raise ValueError("segment sequence must be one or greater")
        if not all(isinstance(value, HL7Field) for value in self.fields):
            raise TypeError("all fields must be HL7Field instances")
        object.__setattr__(self, "fields", tuple(self.fields))

    def field(self, position: int) -> HL7Field:
        """Return an HL7 field using one-based field numbering."""

        if position < 1:
            raise IndexError("HL7 field positions are one-based")
        try:
            return self.fields[position - 1]
        except IndexError as exc:
            raise IndexError(f"field position {position} does not exist in {self.name}") from exc
