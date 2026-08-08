from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.component import HL7Component
from healthcare_pipeline.parsers.hl7.core.constants import HL7_MSH_SEGMENT_NAME
from healthcare_pipeline.parsers.hl7.core.delimiters import HL7Delimiters
from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment


class HL7MessageBuilder:
    """Build immutable HL7 structural objects from normalized message text."""

    def build_message(
        self,
        *,
        raw_value: str,
        normalized_value: str,
    ) -> HL7Message:
        """Build a complete immutable message from raw and normalized text."""

        if not isinstance(raw_value, str) or not raw_value:
            raise InvalidMessageError("raw HL7 message must be a non-empty string")
        if not isinstance(normalized_value, str) or not normalized_value:
            raise InvalidMessageError("normalized HL7 message must be non-empty")

        segment_values = tuple(normalized_value.split("\r"))
        if not segment_values or segment_values[0][:3] != HL7_MSH_SEGMENT_NAME:
            raise InvalidMessageError("HL7 message must begin with an MSH segment")
        if any(segment == "" for segment in segment_values):
            raise InvalidMessageError("HL7 message contains an empty segment")

        try:
            delimiters = HL7Delimiters.from_msh(segment_values[0])
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(str(exc)) from exc

        segments = tuple(
            self.build_segment(
                segment_value,
                sequence=sequence,
                delimiters=delimiters,
            )
            for sequence, segment_value in enumerate(segment_values, start=1)
        )

        return HL7Message(
            raw_value=raw_value,
            delimiters=delimiters,
            segments=segments,
        )

    def build_segment(
        self,
        segment_value: str,
        *,
        sequence: int,
        delimiters: HL7Delimiters,
    ) -> HL7Segment:
        """Build one segment and preserve the sender's field positions."""

        if not isinstance(segment_value, str):
            raise TypeError("segment_value must be a string")
        if len(segment_value) < 3:
            raise InvalidMessageError("HL7 segment must contain a three-character name")

        segment_name = segment_value[:3]
        if len(segment_value) == 3:
            field_values: tuple[str, ...] = ()
        else:
            if segment_value[3] != delimiters.field:
                raise InvalidMessageError(
                    f"segment {segment_name!r} does not use the declared field separator"
                )

            ordinary_field_values = tuple(segment_value[4:].split(delimiters.field))
            if segment_name == HL7_MSH_SEGMENT_NAME:
                # MSH-1 is the field separator itself. Ordinary splitting would
                # otherwise make the encoding characters appear as field one.
                field_values = (delimiters.field, *ordinary_field_values)
            else:
                field_values = ordinary_field_values

        fields = tuple(
            self.build_field(field_value, delimiters=delimiters)
            for field_value in field_values
        )

        try:
            return HL7Segment(
                name=segment_name,
                raw_value=segment_value,
                fields=fields,
                sequence=sequence,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(str(exc)) from exc

    def build_field(
        self,
        field_value: str,
        *,
        delimiters: HL7Delimiters,
    ) -> HL7Field:
        """Build a field including all repetitions, components, and subcomponents."""

        repetitions = tuple(
            self.build_repetition(repetition_value, delimiters=delimiters)
            for repetition_value in field_value.split(delimiters.repetition)
        )
        return HL7Field(raw_value=field_value, repetitions=repetitions)

    def build_repetition(
        self,
        repetition_value: str,
        *,
        delimiters: HL7Delimiters,
    ) -> HL7Repetition:
        """Build one repetition inside an HL7 field."""

        components = tuple(
            self.build_component(component_value, delimiters=delimiters)
            for component_value in repetition_value.split(delimiters.component)
        )
        return HL7Repetition(raw_value=repetition_value, components=components)

    def build_component(
        self,
        component_value: str,
        *,
        delimiters: HL7Delimiters,
    ) -> HL7Component:
        """Build one component while preserving empty subcomponents."""

        subcomponents = tuple(component_value.split(delimiters.subcomponent))
        return HL7Component(
            raw_value=component_value,
            subcomponents=subcomponents,
        )
