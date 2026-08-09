from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.canonical.common.coding import Coding


@dataclass(frozen=True, slots=True)
class Allergy:
    """Canonical allergy/intolerance assertion with coded allergen when available."""

    allergen: Coding
    category: Coding | None = None
    severity: Coding | None = None
    reactions: tuple[str, ...] = ()
    identified_date: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.allergen, Coding):
            raise TypeError("allergen must be a Coding")
        if self.category is not None and not isinstance(self.category, Coding):
            raise TypeError("category must be a Coding or None")
        if self.severity is not None and not isinstance(self.severity, Coding):
            raise TypeError("severity must be a Coding or None")
        reactions = tuple(value.strip() for value in self.reactions if value.strip())
        if len({value.casefold() for value in reactions}) != len(reactions):
            raise ValueError("reactions must not contain duplicates")
        object.__setattr__(self, "reactions", reactions)
