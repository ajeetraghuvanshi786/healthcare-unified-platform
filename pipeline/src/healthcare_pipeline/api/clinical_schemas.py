from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClinicalAPIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClinicalSummaryResponse(ClinicalAPIModel):
    master_patient_id: UUID
    encounter_count: int
    diagnosis_count: int
    observation_count: int
    allergy_count: int
    medication_order_count: int
    medication_administration_count: int
    coverage_count: int
    latest_event_at: datetime | None


class TimelineEventResponse(ClinicalAPIModel):
    event_id: UUID
    event_type: str
    resource_id: UUID
    occurred_at: datetime
    display: str
    details: dict[str, object]


class TimelinePageResponse(ClinicalAPIModel):
    items: list[TimelineEventResponse]
    next_cursor: str | None


class ClinicalResourceResponse(ClinicalAPIModel):
    resource_id: UUID
    resource_type: str
    occurred_at: datetime | date | None
    display: str
    details: dict[str, object]


class ClinicalResourceListResponse(ClinicalAPIModel):
    items: list[ClinicalResourceResponse]


class ClinicalProvenanceResponse(ClinicalAPIModel):
    resource_type: str
    resource_id: UUID
    source_system: str
    source_message_id: str
    source_event_code: str
    recorded_at: datetime
