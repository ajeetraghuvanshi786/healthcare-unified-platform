from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.component import HL7Component


@dataclass(frozen=True, slots=True)
class HL7Repetition:
    """One repetition within an HL7 field."""

    raw_value: str
    components: tuple[HL7Component, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raw_value, str):
            raise TypeError("raw_value must be a string")
        if not self.components:
            raise ValueError("repetition must contain at least one component")
        if not all(isinstance(value, HL7Component) for value in self.components):
            raise TypeError("all components must be HL7Component instances")
        object.__setattr__(self, "components", tuple(self.components))

    def component(self, position: int) -> HL7Component:
        if position < 1:
            raise IndexError("HL7 component positions are one-based")
        try:
            return self.components[position - 1]
        except IndexError as exc:
            raise IndexError(f"component position {position} does not exist") from exc


@dataclass(frozen=True, slots=True)
class HL7Field:
    """One HL7 field, including repetitions and nested components."""

    raw_value: str
    repetitions: tuple[HL7Repetition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raw_value, str):
            raise TypeError("raw_value must be a string")
        if not self.repetitions:
            raise ValueError("field must contain at least one repetition")
        if not all(isinstance(value, HL7Repetition) for value in self.repetitions):
            raise TypeError("all repetitions must be HL7Repetition instances")
        object.__setattr__(self, "repetitions", tuple(self.repetitions))

    @property
    def value(self) -> str:
        return self.raw_value

    def repetition(self, position: int) -> HL7Repetition:
        if position < 1:
            raise IndexError("HL7 repetition positions are one-based")
        try:
            return self.repetitions[position - 1]
        except IndexError as exc:
            raise IndexError(f"repetition position {position} does not exist") from exc

    def component(self, position: int, *, repetition: int = 1) -> HL7Component:
        return self.repetition(repetition).component(position)
