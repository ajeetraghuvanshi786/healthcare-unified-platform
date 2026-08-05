from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.constants import HL7_SEGMENT_TERMINATOR


class HL7MessageNormalizer:
    """Normalize transport line endings while preserving HL7 field content."""

    def normalize(self, message_text: str) -> str:
        """Normalize CRLF and LF segment boundaries to the HL7 CR delimiter.

        Only leading and trailing empty transport lines are removed. Empty
        segments inside a message are retained so structural validation can
        reject them explicitly rather than silently changing the message.
        """

        if not isinstance(message_text, str):
            raise TypeError("message_text must be a string")
        if not message_text:
            raise InvalidMessageError("HL7 message text must not be empty")

        normalized = message_text.replace("\r\n", HL7_SEGMENT_TERMINATOR)
        normalized = normalized.replace("\n", HL7_SEGMENT_TERMINATOR)

        segment_values = normalized.split(HL7_SEGMENT_TERMINATOR)
        while segment_values and segment_values[0] == "":
            segment_values.pop(0)
        while segment_values and segment_values[-1] == "":
            segment_values.pop()

        if not segment_values:
            raise InvalidMessageError("HL7 message contains no segments")

        return HL7_SEGMENT_TERMINATOR.join(segment_values)

    def split_segments(self, normalized_message: str) -> tuple[str, ...]:
        """Split normalized message text into ordered segment strings."""

        if not isinstance(normalized_message, str):
            raise TypeError("normalized_message must be a string")
        if not normalized_message:
            raise InvalidMessageError("normalized HL7 message must not be empty")

        segments = tuple(normalized_message.split(HL7_SEGMENT_TERMINATOR))
        if any(segment == "" for segment in segments):
            raise InvalidMessageError("HL7 message contains an empty segment")

        return segments
