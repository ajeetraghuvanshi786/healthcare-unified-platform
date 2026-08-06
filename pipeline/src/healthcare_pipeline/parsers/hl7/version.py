from __future__ import annotations

import re
from dataclasses import dataclass

_VERSION_PATTERN = re.compile(r"^2\.(?:[1-9]|[1-9][0-9])(?:\.\d+)?$")


@dataclass(frozen=True, slots=True, order=True)
class HL7Version:
    """Validated HL7 v2 version identifier from MSH-12."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("HL7 version must be a string")
        normalized = self.value.strip()
        if not _VERSION_PATTERN.fullmatch(normalized):
            raise ValueError(f"invalid HL7 v2 version: {normalized!r}")
        object.__setattr__(self, "value", normalized)

    @property
    def parts(self) -> tuple[int, ...]:
        return tuple(int(part) for part in self.value.split("."))

    def __str__(self) -> str:
        return self.value
