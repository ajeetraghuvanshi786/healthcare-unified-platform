from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HL7Component:
    """One HL7 component, optionally divided into subcomponents."""

    raw_value: str
    subcomponents: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.raw_value, str):
            raise TypeError("raw_value must be a string")
        if not self.subcomponents:
            raise ValueError("component must contain at least one subcomponent")
        if not all(isinstance(value, str) for value in self.subcomponents):
            raise TypeError("all subcomponents must be strings")
        object.__setattr__(self, "subcomponents", tuple(self.subcomponents))

    @property
    def value(self) -> str:
        return self.raw_value

    def subcomponent(self, position: int) -> str:
        if position < 1:
            raise IndexError("HL7 subcomponent positions are one-based")
        try:
            return self.subcomponents[position - 1]
        except IndexError as exc:
            raise IndexError(f"subcomponent position {position} does not exist") from exc
