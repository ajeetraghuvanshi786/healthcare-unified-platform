from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol

from healthcare_pipeline.identity.keying import IdentityKeyEncoder
from healthcare_pipeline.identity.models import IdentityRecord
from healthcare_pipeline.identity.normalization import PatientIdentityNormalizer


class IdentityCandidateStore(Protocol):
    def upsert(self, record: IdentityRecord) -> None: ...

    def get(self, record_id: str) -> IdentityRecord | None: ...

    def candidate_ids(self, record: IdentityRecord) -> tuple[str, ...]: ...


@dataclass(slots=True)
class InMemoryIdentityCandidateStore:
    """Thread-safe bounded-reference candidate index for tests and single-process deployments."""

    key_encoder: IdentityKeyEncoder
    normalizer: PatientIdentityNormalizer = field(default_factory=PatientIdentityNormalizer)
    max_records_per_key: int = 1000
    _records: dict[str, IdentityRecord] = field(default_factory=dict, init=False, repr=False)
    _record_keys: dict[str, tuple[str, ...]] = field(default_factory=dict, init=False, repr=False)
    _index: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set), init=False, repr=False
    )
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.max_records_per_key, int) or self.max_records_per_key < 1:
            raise ValueError("max_records_per_key must be a positive integer")

    def upsert(self, record: IdentityRecord) -> None:
        if not isinstance(record, IdentityRecord):
            raise TypeError("record must be an IdentityRecord")
        keys = self._candidate_keys(record)
        with self._lock:
            previous_keys = self._record_keys.get(record.record_id, ())
            for key in previous_keys:
                bucket = self._index.get(key)
                if bucket is not None:
                    bucket.discard(record.record_id)
                    if not bucket:
                        self._index.pop(key, None)
            for key in keys:
                bucket = self._index[key]
                if record.record_id not in bucket and len(bucket) >= self.max_records_per_key:
                    continue
                bucket.add(record.record_id)
            self._records[record.record_id] = record
            self._record_keys[record.record_id] = keys

    def get(self, record_id: str) -> IdentityRecord | None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-blank string")
        with self._lock:
            return self._records.get(record_id.strip())

    def candidate_ids(self, record: IdentityRecord) -> tuple[str, ...]:
        keys = self._candidate_keys(record)
        candidates: set[str] = set()
        with self._lock:
            for key in keys:
                candidates.update(self._index.get(key, ()))
        candidates.discard(record.record_id)
        return tuple(sorted(candidates))

    def _candidate_keys(self, record: IdentityRecord) -> tuple[str, ...]:
        normalized = self.normalizer.normalize(record.patient)
        scope_prefix = f"{record.scope.tenant_id}\x1f{record.scope.identity_domain}"
        raw_keys: list[tuple[str, str]] = []
        raw_keys.extend(("identifier", value) for value in normalized.scoped_identifiers)
        if normalized.birth_date is not None:
            raw_keys.extend(
                ("name_dob", f"{name}\x1f{normalized.birth_date}")
                for name in normalized.name_keys
            )
        raw_keys.extend(("phone", value) for value in normalized.phones)
        raw_keys.extend(("email", value) for value in normalized.emails)
        return tuple(
            dict.fromkeys(
                self.key_encoder.encode(f"{scope_prefix}\x1f{kind}", value)
                for kind, value in raw_keys
            )
        )
