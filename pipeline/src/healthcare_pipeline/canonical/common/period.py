from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.canonical.common._validation import ensure_aware


@dataclass(frozen=True, slots=True)
class Period:
    """Timezone-aware interval used by encounters, orders, and other resources."""

    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self) -> None:
        ensure_aware(self.start, "start")
        ensure_aware(self.end, "end")
        if self.start is None and self.end is None:
            raise ValueError("period must include a start or end")
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("period end must not precede start")
