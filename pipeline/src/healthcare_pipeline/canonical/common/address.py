from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_optional


@dataclass(frozen=True, slots=True)
class Address:
    """Source-neutral postal or physical address."""

    lines: tuple[str, ...] = ()
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    district: str | None = None
    use: str | None = None

    def __post_init__(self) -> None:
        lines = tuple(
            value
            for line in self.lines
            if (value := normalize_optional(line, "line")) is not None
        )
        object.__setattr__(self, "lines", lines)
        for field_name in ("city", "state", "postal_code", "country", "district", "use"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if not lines and all(
            getattr(self, field_name) is None
            for field_name in ("city", "state", "postal_code", "country", "district")
        ):
            raise ValueError("address must contain at least one value")
