from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_optional


@dataclass(frozen=True, slots=True)
class HumanName:
    """Source-neutral human name preserving structured components."""

    family: str | None = None
    given: tuple[str, ...] = ()
    prefix: tuple[str, ...] = ()
    suffix: tuple[str, ...] = ()
    use: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", normalize_optional(self.family, "family"))
        object.__setattr__(self, "use", normalize_optional(self.use, "use"))
        for field_name in ("given", "prefix", "suffix"):
            normalized = tuple(
                value
                for item in getattr(self, field_name)
                if (value := normalize_optional(item, field_name)) is not None
            )
            object.__setattr__(self, field_name, normalized)
        if self.family is None and not self.given:
            raise ValueError("human name must include a family or given name")

    @property
    def display(self) -> str:
        parts = (*self.prefix, *self.given, self.family, *self.suffix)
        return " ".join(part for part in parts if part is not None)
