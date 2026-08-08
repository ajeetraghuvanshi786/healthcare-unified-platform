from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class Allergy:
    """Immutable semantic allergy or intolerance representation from AL1."""

    set_id: int
    allergen: CodedValue
    allergy_type: CodedValue | None = None
    severity: CodedValue | None = None
    reactions: tuple[str, ...] = ()
    identification_date: date | None = None

    def __post_init__(self) -> None:
        if self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        if not isinstance(self.allergen, CodedValue):
            raise TypeError("allergen must be a CodedValue")
        if self.allergy_type is not None and not isinstance(self.allergy_type, CodedValue):
            raise TypeError("allergy_type must be a CodedValue or None")
        if self.severity is not None and not isinstance(self.severity, CodedValue):
            raise TypeError("severity must be a CodedValue or None")

        normalized_reactions = tuple(
            reaction
            for value in self.reactions
            if (reaction := normalize_optional(value, "reaction")) is not None
        )
        reaction_keys = {value.casefold() for value in normalized_reactions}
        if len(normalized_reactions) != len(reaction_keys):
            raise ValueError("reactions must not contain duplicates")
        object.__setattr__(self, "reactions", normalized_reactions)
