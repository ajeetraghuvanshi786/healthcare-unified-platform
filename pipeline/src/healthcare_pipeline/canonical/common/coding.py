from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_optional


@dataclass(frozen=True, slots=True)
class Coding:
    """Source-neutral coded concept suitable for terminology normalization later."""

    code: str | None = None
    display: str | None = None
    system: str | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("code", "display", "system", "version"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if self.code is None and self.display is None:
            raise ValueError("coding must include a code or display")

    @property
    def key(self) -> tuple[str | None, str | None]:
        system = self.system.casefold() if self.system is not None else None
        return system, self.code
