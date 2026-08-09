from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import (
    normalize_optional,
    normalize_required,
)


@dataclass(frozen=True, slots=True)
class Identifier:
    """Source-neutral identifier scoped by an optional namespace/system."""

    value: str
    system: str | None = None
    type_code: str | None = None
    assigner: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_required(self.value, "value"))
        for field_name in ("system", "type_code", "assigner"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )

    @property
    def identity_key(self) -> tuple[str | None, str, str | None]:
        system = self.system.casefold() if self.system is not None else None
        type_code = self.type_code.upper() if self.type_code is not None else None
        return system, self.value, type_code
