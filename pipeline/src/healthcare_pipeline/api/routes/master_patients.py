from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError

from healthcare_pipeline.api.dependencies import DatabaseSession, Runtime
from healthcare_pipeline.api.schemas import (
    MasterPatientLinkResponse,
    MasterPatientResponse,
    ReviewApprovalRequest,
    ReviewCaseResponse,
    ReviewDecisionResponse,
)
from healthcare_pipeline.api.security import RequestIdentityContext, require_request_identity
from healthcare_pipeline.identity.master.sqlalchemy_repository import (
    SQLAlchemyMasterIdentityRepository,
)

router = APIRouter(prefix="/api/v1", tags=["identity"])


@router.get("/master-patients/{master_patient_id}", response_model=MasterPatientResponse)
def get_master_patient(
    master_patient_id: UUID,
    session: DatabaseSession,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> MasterPatientResponse:
    repository = SQLAlchemyMasterIdentityRepository(session)
    master = repository.get_master(master_patient_id)
    if master is None or master.scope != context.scope:
        raise HTTPException(status_code=404, detail="Master patient not found")
    links = repository.active_links_for_master(master_patient_id)
    return MasterPatientResponse(
        master_patient_id=master.master_patient_id,
        tenant_id=master.scope.tenant_id,
        identity_domain=master.scope.identity_domain,
        links=[
            MasterPatientLinkResponse(
                source_system=link.source_system,
                source_record_id=link.source_record_id,
                status=link.status.value,
            )
            for link in links
        ],
    )


@router.get("/identity/reviews/{review_case_id}", response_model=ReviewCaseResponse)
def get_review_case(
    review_case_id: UUID,
    session: DatabaseSession,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ReviewCaseResponse:
    repository = SQLAlchemyMasterIdentityRepository(session)
    review = repository.get_review_case(review_case_id)
    if review is None or review.scope != context.scope:
        raise HTTPException(status_code=404, detail="Review case not found")
    return ReviewCaseResponse(
        review_case_id=review.review_case_id,
        tenant_id=review.scope.tenant_id,
        identity_domain=review.scope.identity_domain,
        source_record_id=review.source_record_id,
        candidate_record_ids=list(review.candidate_record_ids),
        resolution_status=review.resolution_status.value,
        status=review.status.value,
    )


@router.post(
    "/identity/reviews/{review_case_id}/approve",
    response_model=ReviewDecisionResponse,
)
def approve_review(
    review_case_id: UUID,
    request: ReviewApprovalRequest,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ReviewDecisionResponse:
    try:
        link = runtime.identity_review_service(session).approve(
            review_case_id,
            candidate_record_id=request.candidate_record_id,
            scope=context.scope,
            actor_id=context.actor_id,
        )
        session.commit()
    except (IntegrityError, StaleDataError, ValueError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review approval could not be applied",
        ) from exc
    except OperationalError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc

    return ReviewDecisionResponse(
        review_case_id=review_case_id,
        status="approved",
        master_patient_id=link.master_patient_id,
    )


@router.post(
    "/identity/reviews/{review_case_id}/reject",
    response_model=ReviewDecisionResponse,
)
def reject_review(
    review_case_id: UUID,
    session: DatabaseSession,
    runtime: Runtime,
    context: Annotated[RequestIdentityContext, Depends(require_request_identity)],
) -> ReviewDecisionResponse:
    try:
        review = runtime.identity_review_service(session).reject(
            review_case_id,
            scope=context.scope,
            actor_id=context.actor_id,
        )
        session.commit()
    except (IntegrityError, StaleDataError, ValueError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review rejection could not be applied",
        ) from exc
    except OperationalError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is temporarily unavailable",
        ) from exc

    return ReviewDecisionResponse(
        review_case_id=review.review_case_id,
        status=review.status.value,
    )
