from __future__ import annotations

import re
from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,
)

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.delimiters import HL7Delimiters
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.message_header.header import HL7MessageHeader
from healthcare_pipeline.parsers.hl7.message_header.message_type import HL7MessageType
from healthcare_pipeline.parsers.hl7.message_header.processing_id import HL7ProcessingId
from healthcare_pipeline.parsers.hl7.message_header.version import HL7Version

_TIMESTAMP_PATTERN = re.compile(
    r"^(?P<value>\d{4}(?:\d{2}){0,5})(?:\.(?P<fraction>\d{1,4}))?"
    r"(?P<offset>[+-]\d{4})?$"
)


class MSHParser:
    """Parse the structural MSH segment into a typed semantic header."""

    def parse_message(self, message: HL7Message) -> HL7MessageHeader:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return self.parse_segment(message.segment("MSH"), delimiters=message.delimiters)

    def parse_segment(
        self,
        segment: HL7Segment,
        *,
        delimiters: HL7Delimiters,
    ) -> HL7MessageHeader:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "MSH":
            raise InvalidMessageError("MSH parser requires an MSH segment")

        try:
            message_type = self._parse_message_type(segment)
            processing_id = self._parse_processing_id(segment)
            version = HL7Version(self._required_field(segment, 12, "HL7 version"))
            message_datetime = self._parse_timestamp(
                self._required_field(segment, 7, "message datetime")
            )

            return HL7MessageHeader(
                delimiters=delimiters,
                sending_application=self._required_field(
                    segment, 3, "sending application"
                ),
                sending_facility=self._required_field(
                    segment, 4, "sending facility"
                ),
                receiving_application=self._required_field(
                    segment, 5, "receiving application"
                ),
                receiving_facility=self._required_field(
                    segment, 6, "receiving facility"
                ),
                message_datetime=message_datetime,
                security=self._optional_field(segment, 8),
                message_type=message_type,
                message_control_id=self._required_field(
                    segment, 10, "message control ID"
                ),
                processing_id=processing_id,
                version=version,
                sequence_number=self._optional_field(segment, 13),
                continuation_pointer=self._optional_field(segment, 14),
                accept_acknowledgment_type=self._optional_field(segment, 15),
                application_acknowledgment_type=self._optional_field(segment, 16),
                country_code=self._optional_field(segment, 17),
                character_set=self._optional_field(segment, 18),
                principal_language=self._optional_field(segment, 19),
            )
        except (IndexError, TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid MSH segment: {exc}") from exc

    @staticmethod
    def _required_field(segment: HL7Segment, position: int, label: str) -> str:
        value = segment.field(position).value.strip()
        if not value:
            raise ValueError(f"MSH-{position} {label} is required")
        return value

    @staticmethod
    def _optional_field(segment: HL7Segment, position: int) -> str | None:
        try:
            value = segment.field(position).value.strip()
        except IndexError:
            return None
        return value or None

    def _parse_message_type(self, segment: HL7Segment) -> HL7MessageType:
        field = segment.field(9)
        message_code = field.component(1).value
        trigger_event = field.component(2).value
        try:
            message_structure = field.component(3).value or None
        except IndexError:
            message_structure = None
        return HL7MessageType(
            message_code=message_code,
            trigger_event=trigger_event,
            message_structure=message_structure,
        )

    def _parse_processing_id(self, segment: HL7Segment) -> HL7ProcessingId:
        field = segment.field(11)
        mode = field.component(1).value
        try:
            processing_version = field.component(2).value or None
        except IndexError:
            processing_version = None
        return HL7ProcessingId.from_code(
            mode,
            processing_version=processing_version,
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        match = _TIMESTAMP_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"invalid HL7 timestamp: {value!r}")

        digits = match.group("value")
        if len(digits) not in {4, 6, 8, 10, 12, 14}:
            raise ValueError(f"unsupported HL7 timestamp precision: {value!r}")

        padded = digits.ljust(14, "0")
        parsed = datetime.strptime(padded, "%Y%m%d%H%M%S")

        fraction = match.group("fraction")
        if fraction:
            parsed = parsed.replace(microsecond=int(fraction.ljust(6, "0")))

        offset = match.group("offset")
        if offset:
            sign = 1 if offset[0] == "+" else -1
            hours = int(offset[1:3])
            minutes = int(offset[3:5])
            if hours > 23 or minutes > 59:
                raise ValueError(f"invalid HL7 timezone offset: {offset}")
            parsed = parsed.replace(
                tzinfo=timezone(sign * timedelta(hours=hours, minutes=minutes))
            )
        else:
            parsed = parsed.replace(tzinfo=UTC)

        return parsed
