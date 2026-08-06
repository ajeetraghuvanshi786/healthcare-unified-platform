from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class CodedValue:
    """Source-preserving HL7 coded value, typically from CE/CWE fields."""

    identifier: str | None = None
    text: str | None = None
    coding_system: str | None = None
    alternate_identifier: str | None = None
    alternate_text: str | None = None
    alternate_coding_system: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "identifier",
            "text",
            "coding_system",
            "alternate_identifier",
            "alternate_text",
            "alternate_coding_system",
        ):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if self.identifier is None and self.text is None:
            raise ValueError("coded value must include an identifier or text")

    @property
    def display(self) -> str:
        return self.text or self.identifier or ""
