from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HL7ProcessRequest(APIModel):
    source_system: Annotated[str, Field(min_length=1, max_length=128)]
    hl7: Annotated[str, Field(min_length=1, max_length=16_777_216)]


class ProcessingResponse(APIModel):
    status: str
    source_message_id: str
    source_event_code: str
    validation_error_count: int
    validation_warning_count: int
    terminology_status_counts: dict[str, int]
    identity_status: str | None = None
    source_record_id: str | None = None
    master_patient_id: UUID | None = None
    review_case_id: UUID | None = None


class MasterPatientLinkResponse(APIModel):
    source_system: str
    source_record_id: str
    status: str


class MasterPatientResponse(APIModel):
    master_patient_id: UUID
    tenant_id: str
    identity_domain: str
    links: list[MasterPatientLinkResponse]


class ReviewCaseResponse(APIModel):
    review_case_id: UUID
    tenant_id: str
    identity_domain: str
    source_record_id: str
    candidate_record_ids: list[str]
    resolution_status: str
    status: str


class ReviewApprovalRequest(APIModel):
    candidate_record_id: Annotated[str, Field(min_length=1, max_length=128)]


class ReviewDecisionResponse(APIModel):
    review_case_id: UUID
    status: str
    master_patient_id: UUID | None = None
