from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock

from healthcare_pipeline.terminology.models import CodeValidationResult

type ValidationCacheKey = tuple[str, str, str | None, str]


@dataclass(slots=True)
class TerminologyValidationCache:
    """Thread-safe bounded LRU cache for terminology-validation responses."""

    max_entries: int = 4096
    _entries: OrderedDict[ValidationCacheKey, CodeValidationResult] = field(
        init=False,
        repr=False,
    )
    _lock: RLock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.max_entries, bool) or not isinstance(self.max_entries, int):
            raise TypeError("max_entries must be an integer")
        if self.max_entries < 1:
            raise ValueError("max_entries must be greater than zero")
        self._entries = OrderedDict()
        self._lock = RLock()

    def get(self, key: ValidationCacheKey) -> CodeValidationResult | None:
        with self._lock:
            result = self._entries.get(key)
            if result is not None:
                self._entries.move_to_end(key)
            return result

    def put(self, key: ValidationCacheKey, value: CodeValidationResult) -> None:
        with self._lock:
            self._entries[key] = value
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)
