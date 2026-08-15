from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID


class ClinicalWriteStatus(StrEnum):
    CREATED = "created"
    ALREADY_PROCESSED = "already_processed"


@dataclass(frozen=True, slots=True)
class ClinicalWriteResult:
    status: ClinicalWriteStatus
    clinical_message_id: UUID


@dataclass(frozen=True, slots=True)
class PatientClinicalSummary:
    master_patient_id: UUID
    encounter_count: int
    diagnosis_count: int
    observation_count: int
    allergy_count: int
    medication_order_count: int
    medication_administration_count: int
    coverage_count: int
    latest_event_at: datetime | None


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    event_id: UUID
    event_type: str
    resource_id: UUID
    occurred_at: datetime
    display: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class TimelinePage:
    items: tuple[TimelineEvent, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class ClinicalListItem:
    resource_id: UUID
    resource_type: str
    occurred_at: datetime | date | None
    display: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class ClinicalProvenance:
    resource_type: str
    resource_id: UUID
    source_system: str
    source_message_id: str
    source_event_code: str
    recorded_at: datetime
