from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError

from healthcare_pipeline.api.dependencies import DatabaseSession, Runtime
from healthcare_pipeline.api.schemas import HL7ProcessRequest, ProcessingResponse
from healthcare_pipeline.api.security import RequestIdentityContext, require_request_identity
from healthcare_pipeline.parsers.exceptions import InvalidMessageError, InvalidPayloadError

router = APIRouter(prefix="/api/v1", tags=["processing"])


@router.post("/hl7/process", response_model=ProcessingResponse)
def process_hl7(
    request: HL7ProcessRequest,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ProcessingResponse:
    service = runtime.processing_service(session)
    payload = request.hl7.encode()
    try:
        outcome = service.process_hl7(
            payload,
            source_system=request.source_system,
            scope=context.scope,
            actor_id=context.actor_id,
        )
        session.commit()
    except (InvalidPayloadError, InvalidMessageError, ValueError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="HL7 payload is invalid or violates supported processing rules",
        ) from exc
    except (IntegrityError, StaleDataError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent identity update conflict; retry the request",
        ) from exc
    except OperationalError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc

    return ProcessingResponse(
        status=outcome.status.value,
        source_message_id=outcome.source_message_id,
        source_event_code=outcome.source_event_code,
        validation_error_count=outcome.validation_error_count,
        validation_warning_count=outcome.validation_warning_count,
        terminology_status_counts=dict(outcome.terminology_status_counts),
        identity_status=outcome.identity_status.value if outcome.identity_status else None,
        source_record_id=outcome.source_record_id,
        master_patient_id=outcome.master_patient_id,
        review_case_id=outcome.review_case_id,
    )
