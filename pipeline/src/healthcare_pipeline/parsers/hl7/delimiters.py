from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.constants import (
    HL7_DEFAULT_COMPONENT_SEPARATOR,
    HL7_DEFAULT_ENCODING_CHARACTERS,
    HL7_DEFAULT_ESCAPE_CHARACTER,
    HL7_DEFAULT_FIELD_SEPARATOR,
    HL7_DEFAULT_REPETITION_SEPARATOR,
    HL7_DEFAULT_SUBCOMPONENT_SEPARATOR,
    HL7_MINIMUM_MSH_LENGTH,
    HL7_MSH_SEGMENT_NAME,
    HL7_RESERVED_DELIMITER_CHARACTERS,
)


@dataclass(frozen=True, slots=True)
class HL7Delimiters:
    """Immutable delimiter set declared by the HL7 MSH segment."""

    field: str = HL7_DEFAULT_FIELD_SEPARATOR
    component: str = HL7_DEFAULT_COMPONENT_SEPARATOR
    repetition: str = HL7_DEFAULT_REPETITION_SEPARATOR
    escape: str = HL7_DEFAULT_ESCAPE_CHARACTER
    subcomponent: str = HL7_DEFAULT_SUBCOMPONENT_SEPARATOR

    def __post_init__(self) -> None:
        values = {
            "field": self.field,
            "component": self.component,
            "repetition": self.repetition,
            "escape": self.escape,
            "subcomponent": self.subcomponent,
        }

        for name, value in values.items():
            if not isinstance(value, str):
                raise TypeError(f"{name} delimiter must be a string")
            if len(value) != 1:
                raise ValueError(f"{name} delimiter must contain exactly one character")
            if value in HL7_RESERVED_DELIMITER_CHARACTERS:
                raise ValueError(f"{name} delimiter contains a reserved control character")

        if len(set(values.values())) != len(values):
            raise ValueError("HL7 delimiters must be unique")

    @property
    def encoding_characters(self) -> str:
        """Return MSH-2 encoding characters in HL7-defined order."""

        return f"{self.component}{self.repetition}{self.escape}{self.subcomponent}"

    @classmethod
    def default(cls) -> HL7Delimiters:
        return cls()

    @classmethod
    def from_msh(cls, msh_segment: str) -> HL7Delimiters:
        """Extract delimiters from the beginning of an MSH segment.

        HL7 defines MSH-1 at character position four and MSH-2 in the next
        four characters. This extraction must occur before ordinary field
        splitting because MSH itself declares the separators.
        """

        if not isinstance(msh_segment, str):
            raise TypeError("msh_segment must be a string")
        if len(msh_segment) < HL7_MINIMUM_MSH_LENGTH:
            raise ValueError("MSH segment is too short to declare HL7 delimiters")
        if not msh_segment.startswith(HL7_MSH_SEGMENT_NAME):
            raise ValueError("HL7 message must begin with an MSH segment")

        field = msh_segment[3]
        encoding_characters = msh_segment[4:8]
        if len(encoding_characters) != len(HL7_DEFAULT_ENCODING_CHARACTERS):
            raise ValueError("MSH-2 must contain four encoding characters")

        return cls(
            field=field,
            component=encoding_characters[0],
            repetition=encoding_characters[1],
            escape=encoding_characters[2],
            subcomponent=encoding_characters[3],
        )
