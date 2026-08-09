from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import ensure_aware, normalize_required
from healthcare_pipeline.canonical.common.coding import Coding


@dataclass(frozen=True, slots=True)
class Observation:
    """Canonical clinical measurement, finding, or result."""

    code: Coding
    values: tuple[str, ...]
    status: str
    value_type: str
    units: Coding | None = None
    reference_range: str | None = None
    abnormal_flags: tuple[str, ...] = ()
    effective_datetime: datetime | None = None
    performers: tuple[Provider, ...] = ()
    methods: tuple[Coding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.code, Coding):
            raise TypeError("code must be a Coding")
        values = tuple(value.strip() for value in self.values if value.strip())
        if not values:
            raise ValueError("values must contain at least one value")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "status", normalize_required(self.status, "status").upper())
        object.__setattr__(
            self,
            "value_type",
            normalize_required(self.value_type, "value_type").upper(),
        )
        ensure_aware(self.effective_datetime, "effective_datetime")
        for field_name, expected_type in (("performers", Provider), ("methods", Coding)):
            items = tuple(getattr(self, field_name))
            if not all(isinstance(item, expected_type) for item in items):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, items)
        object.__setattr__(
            self,
            "abnormal_flags",
            tuple(value.strip() for value in self.abnormal_flags if value.strip()),
        )
