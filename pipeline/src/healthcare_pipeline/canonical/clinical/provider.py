from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common.human_name import HumanName
from healthcare_pipeline.canonical.common.identifier import Identifier


@dataclass(frozen=True, slots=True)
class Provider:
    """Canonical clinician or other healthcare provider identity."""

    identifiers: tuple[Identifier, ...] = ()
    names: tuple[HumanName, ...] = ()
    qualifications: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        identifiers = tuple(self.identifiers)
        names = tuple(self.names)
        qualifications = tuple(value.strip() for value in self.qualifications if value.strip())
        if not all(isinstance(value, Identifier) for value in identifiers):
            raise TypeError("identifiers must contain Identifier values")
        if not all(isinstance(value, HumanName) for value in names):
            raise TypeError("names must contain HumanName values")
        if not identifiers and not names:
            raise ValueError("provider must include an identifier or name")
        object.__setattr__(self, "identifiers", identifiers)
        object.__setattr__(self, "names", names)
        object.__setattr__(self, "qualifications", qualifications)
