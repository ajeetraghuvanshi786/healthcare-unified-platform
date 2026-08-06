from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.delimiters import HL7Delimiters
from healthcare_pipeline.parsers.hl7.message_type import HL7MessageType
from healthcare_pipeline.parsers.hl7.processing_id import HL7ProcessingId
from healthcare_pipeline.parsers.hl7.version import HL7Version


@dataclass(frozen=True, slots=True)
class HL7MessageHeader:
    """Typed semantic representation of an HL7 MSH segment."""

    delimiters: HL7Delimiters
    sending_application: str
    sending_facility: str
    receiving_application: str
    receiving_facility: str
    message_datetime: datetime
    security: str | None
    message_type: HL7MessageType
    message_control_id: str
    processing_id: HL7ProcessingId
    version: HL7Version
    sequence_number: str | None = None
    continuation_pointer: str | None = None
    accept_acknowledgment_type: str | None = None
    application_acknowledgment_type: str | None = None
    country_code: str | None = None
    character_set: str | None = None
    principal_language: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.delimiters, HL7Delimiters):
            raise TypeError("delimiters must be an HL7Delimiters instance")
        if not isinstance(self.message_datetime, datetime):
            raise TypeError("message_datetime must be a datetime")
        if self.message_datetime.tzinfo is None:
            raise ValueError("message_datetime must be timezone-aware")
        if not isinstance(self.message_type, HL7MessageType):
            raise TypeError("message_type must be an HL7MessageType")
        if not isinstance(self.processing_id, HL7ProcessingId):
            raise TypeError("processing_id must be an HL7ProcessingId")
        if not isinstance(self.version, HL7Version):
            raise TypeError("version must be an HL7Version")

        required_fields = (
            "sending_application",
            "sending_facility",
            "receiving_application",
            "receiving_facility",
            "message_control_id",
        )
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            normalized = value.strip()
            if not normalized:
                raise ValueError(f"{field_name} must not be blank")
            object.__setattr__(self, field_name, normalized)

        optional_fields = (
            "security",
            "sequence_number",
            "continuation_pointer",
            "accept_acknowledgment_type",
            "application_acknowledgment_type",
            "country_code",
            "character_set",
            "principal_language",
        )
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                if not isinstance(value, str):
                    raise TypeError(f"{field_name} must be a string or None")
                object.__setattr__(self, field_name, value.strip() or None)
