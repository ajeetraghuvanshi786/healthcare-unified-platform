from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from healthcare_pipeline.canonical.common._validation import ensure_non_negative
from healthcare_pipeline.canonical.common.coding import Coding


@dataclass(frozen=True, slots=True)
class Quantity:
    """Exact decimal quantity with an optional coded unit."""

    value: Decimal
    unit: Coding | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise TypeError("value must be a Decimal")
        ensure_non_negative(self.value, "value")
        if self.unit is not None and not isinstance(self.unit, Coding):
            raise TypeError("unit must be a Coding or None")
