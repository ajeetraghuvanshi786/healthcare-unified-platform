from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from healthcare_pipeline.canonical.common._validation import (
    normalize_optional,
    normalize_required,
)


class ContactPointSystem(StrEnum):
    PHONE = "phone"
    EMAIL = "email"
    FAX = "fax"
    PAGER = "pager"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ContactPoint:
    """Source-neutral telephone, email, fax, pager, or other contact value."""

    system: ContactPointSystem
    value: str
    use: str | None = None
    rank: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.system, ContactPointSystem):
            raise TypeError("system must be a ContactPointSystem")
        object.__setattr__(self, "value", normalize_required(self.value, "value"))
        object.__setattr__(self, "use", normalize_optional(self.use, "use"))
        if self.rank is not None and (not isinstance(self.rank, int) or self.rank < 1):
            raise ValueError("rank must be a positive integer or None")
