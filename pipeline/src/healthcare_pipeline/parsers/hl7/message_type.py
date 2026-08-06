from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HL7MessageType:
    """Semantic representation of MSH-9 message type information."""

    message_code: str
    trigger_event: str
    message_structure: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("message_code", self.message_code),
            ("trigger_event", self.trigger_event),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if not value.strip():
                raise ValueError(f"{field_name} must not be blank")

        normalized_code = self.message_code.strip().upper()
        normalized_trigger = self.trigger_event.strip().upper()
        if not normalized_code.isalnum():
            raise ValueError("message_code must be uppercase alphanumeric")
        if not normalized_trigger.isalnum():
            raise ValueError("trigger_event must be uppercase alphanumeric")

        object.__setattr__(self, "message_code", normalized_code)
        object.__setattr__(self, "trigger_event", normalized_trigger)

        if self.message_structure is not None:
            if not isinstance(self.message_structure, str):
                raise TypeError("message_structure must be a string or None")
            normalized_structure = self.message_structure.strip().upper()
            if not normalized_structure:
                object.__setattr__(self, "message_structure", None)
            else:
                object.__setattr__(self, "message_structure", normalized_structure)

    @property
    def event_code(self) -> str:
        """Return the conventional combined message and trigger code."""

        return f"{self.message_code}^{self.trigger_event}"
