from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import OperationalError

from healthcare_pipeline.api.clinical_schemas import (
    ClinicalProvenanceResponse,
    ClinicalResourceListResponse,
    ClinicalResourceResponse,
    ClinicalSummaryResponse,
    TimelineEventResponse,
    TimelinePageResponse,
)
from healthcare_pipeline.api.dependencies import DatabaseSession, Runtime
from healthcare_pipeline.api.security import RequestIdentityContext, require_request_identity
from healthcare_pipeline.identity.master.sqlalchemy_repository import (
    SQLAlchemyMasterIdentityRepository,
)

router = APIRouter(prefix="/api/v1", tags=["clinical"])

_RESOURCE_TYPES = {
    "encounters": "encounter",
    "diagnoses": "diagnosis",
    "observations": "observation",
    "allergies": "allergy",
    "medication-orders": "medication_order",
    "medication-administrations": "medication_administration",
    "coverages": "coverage",
}


def _ensure_master_patient(
    master_patient_id: UUID,
    session: DatabaseSession,
    context: RequestIdentityContext,
) -> None:
    master = SQLAlchemyMasterIdentityRepository(session).get_master(master_patient_id)
    if master is None or master.scope != context.scope:
        raise HTTPException(status_code=404, detail="Master patient not found")


@router.get(
    "/master-patients/{master_patient_id}/clinical-summary",
    response_model=ClinicalSummaryResponse,
)
def get_clinical_summary(
    master_patient_id: UUID,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ClinicalSummaryResponse:
    _ensure_master_patient(master_patient_id, session, context)
    try:
        summary = runtime.longitudinal_clinical_service(session).summary(
            master_patient_id=master_patient_id,
            scope=context.scope,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc
    return ClinicalSummaryResponse(
        master_patient_id=summary.master_patient_id,
        encounter_count=summary.encounter_count,
        diagnosis_count=summary.diagnosis_count,
        observation_count=summary.observation_count,
        allergy_count=summary.allergy_count,
        medication_order_count=summary.medication_order_count,
        medication_administration_count=summary.medication_administration_count,
        coverage_count=summary.coverage_count,
        latest_event_at=summary.latest_event_at,
    )


@router.get(
    "/master-patients/{master_patient_id}/timeline",
    response_model=TimelinePageResponse,
)
def get_patient_timeline(
    master_patient_id: UUID,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
) -> TimelinePageResponse:
    _ensure_master_patient(master_patient_id, session, context)
    try:
        page = runtime.longitudinal_clinical_service(session).timeline(
            master_patient_id=master_patient_id,
            scope=context.scope,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid timeline cursor") from exc
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc
    return TimelinePageResponse(
        items=[
            TimelineEventResponse(
                event_id=item.event_id,
                event_type=item.event_type,
                resource_id=item.resource_id,
                occurred_at=item.occurred_at,
                display=item.display,
                details=item.details,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/master-patients/{master_patient_id}/clinical/{resource_collection}",
    response_model=ClinicalResourceListResponse,
)
def list_clinical_resources(
    master_patient_id: UUID,
    resource_collection: str,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ClinicalResourceListResponse:
    resource_type = _RESOURCE_TYPES.get(resource_collection)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Clinical resource collection not found")
    _ensure_master_patient(master_patient_id, session, context)
    try:
        items = runtime.longitudinal_clinical_service(session).resources(
            resource_type=resource_type,
            master_patient_id=master_patient_id,
            scope=context.scope,
            limit=limit,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc
    return ClinicalResourceListResponse(
        items=[
            ClinicalResourceResponse(
                resource_id=item.resource_id,
                resource_type=item.resource_type,
                occurred_at=item.occurred_at,
                display=item.display,
                details=item.details,
            )
            for item in items
        ]
    )


@router.get(
    "/master-patients/{master_patient_id}/clinical/{resource_collection}/"
    "{resource_id}/provenance",
    response_model=ClinicalProvenanceResponse,
)
def get_clinical_provenance(
    master_patient_id: UUID,
    resource_collection: str,
    resource_id: UUID,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ClinicalProvenanceResponse:
    resource_type = _RESOURCE_TYPES.get(resource_collection)
    if resource_type is None:
        raise HTTPException(status_code=404, detail="Clinical resource collection not found")
    _ensure_master_patient(master_patient_id, session, context)
    try:
        provenance = runtime.longitudinal_clinical_service(session).provenance(
            resource_type=resource_type,
            resource_id=resource_id,
            master_patient_id=master_patient_id,
            scope=context.scope,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc
    if provenance is None:
        raise HTTPException(status_code=404, detail="Clinical resource provenance not found")
    return ClinicalProvenanceResponse(
        resource_type=provenance.resource_type,
        resource_id=provenance.resource_id,
        source_system=provenance.source_system,
        source_message_id=provenance.source_message_id,
        source_event_code=provenance.source_event_code,
        recorded_at=provenance.recorded_at,
    )
