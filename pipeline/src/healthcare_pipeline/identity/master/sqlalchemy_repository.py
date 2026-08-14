from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from healthcare_pipeline.identity.master.models import (
    IdentityDecisionAction,
    IdentityDecisionEvent,
    IdentityDecisionReason,
    MasterPatient,
    MasterPatientLink,
    MasterPatientLinkStatus,
    ReviewCase,
    ReviewCaseStatus,
)
from healthcare_pipeline.identity.master.repository import MasterIdentityRepository
from healthcare_pipeline.identity.models import IdentityResolutionStatus, IdentityScope
from healthcare_pipeline.models.identity_master import (
    IdentityDecisionEventModel,
    IdentityReviewCaseModel,
    MasterPatientLinkModel,
    MasterPatientModel,
)


def _required_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value


def _optional_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _required_aware(value)


@dataclass(slots=True)
class SQLAlchemyMasterIdentityRepository(MasterIdentityRepository):
    """Transaction-scoped PostgreSQL/SQLAlchemy adapter for master identity lifecycle."""

    session: Session

    def create_master(self, master: MasterPatient) -> None:
        existing = self.session.get(MasterPatientModel, master.master_patient_id)
        if existing is not None:
            existing_scope = IdentityScope(existing.tenant_id, existing.identity_domain)
            if existing_scope != master.scope:
                raise ValueError("master_patient_id already exists in a different identity scope")
            return
        self.session.add(
            MasterPatientModel(
                id=master.master_patient_id,
                tenant_id=master.scope.tenant_id,
                identity_domain=master.scope.identity_domain,
                version=1,
                created_at=master.created_at,
                updated_at=master.created_at,
            )
        )
        self.session.flush()

    def get_master(self, master_patient_id: UUID) -> MasterPatient | None:
        row = self.session.get(MasterPatientModel, master_patient_id)
        if row is None:
            return None
        return MasterPatient(
            scope=IdentityScope(row.tenant_id, row.identity_domain),
            master_patient_id=row.id,
            created_at=_required_aware(row.created_at)
        )

    def active_link_for_record(
        self,
        *,
        scope: IdentityScope,
        source_record_id: str,
        source_system: str | None = None,
    ) -> MasterPatientLink | None:
        statement = select(MasterPatientLinkModel).where(
            MasterPatientLinkModel.tenant_id == scope.tenant_id,
            MasterPatientLinkModel.identity_domain == scope.identity_domain,
            MasterPatientLinkModel.source_record_id == source_record_id.strip(),
            MasterPatientLinkModel.status == MasterPatientLinkStatus.ACTIVE.value,
        )
        if source_system is not None:
            statement = statement.where(
                MasterPatientLinkModel.source_system == source_system.strip()
            )
        rows = self.session.scalars(statement.limit(2)).all()
        if len(rows) > 1:
            raise ValueError("source_record_id is ambiguous across source systems")
        return self._link(rows[0]) if rows else None

    def active_links_for_master(self, master_patient_id: UUID) -> tuple[MasterPatientLink, ...]:
        rows = self.session.scalars(
            select(MasterPatientLinkModel)
            .where(
                MasterPatientLinkModel.master_patient_id == master_patient_id,
                MasterPatientLinkModel.status == MasterPatientLinkStatus.ACTIVE.value,
            )
            .order_by(
                MasterPatientLinkModel.source_system,
                MasterPatientLinkModel.source_record_id,
            )
        ).all()
        return tuple(self._link(row) for row in rows)

    def save_link(self, link: MasterPatientLink) -> None:
        if link.status is MasterPatientLinkStatus.ACTIVE:
            current = self.active_link_for_record(
                scope=link.scope,
                source_record_id=link.source_record_id,
                source_system=link.source_system,
            )
            if current is not None:
                if current.master_patient_id != link.master_patient_id:
                    raise ValueError("source record is already linked to another master patient")
                return
            self.session.add(
                MasterPatientLinkModel(
                    master_patient_id=link.master_patient_id,
                    tenant_id=link.scope.tenant_id,
                    identity_domain=link.scope.identity_domain,
                    source_system=link.source_system,
                    source_record_id=link.source_record_id,
                    status=link.status.value,
                    linked_at=link.linked_at,
                    unlinked_at=None,
                )
            )
            self.session.flush()
            return

        row = self.session.scalar(
            select(MasterPatientLinkModel)
            .where(
                MasterPatientLinkModel.master_patient_id == link.master_patient_id,
                MasterPatientLinkModel.tenant_id == link.scope.tenant_id,
                MasterPatientLinkModel.identity_domain == link.scope.identity_domain,
                MasterPatientLinkModel.source_system == link.source_system,
                MasterPatientLinkModel.source_record_id == link.source_record_id,
                MasterPatientLinkModel.status == MasterPatientLinkStatus.ACTIVE.value,
            )
            .with_for_update()
        )
        if row is None:
            raise ValueError("active link does not exist")
        row.status = MasterPatientLinkStatus.UNLINKED.value
        row.unlinked_at = link.unlinked_at
        self.session.flush()

    def save_review_case(self, review_case: ReviewCase) -> None:
        row = self.session.get(IdentityReviewCaseModel, review_case.review_case_id)
        if row is None:
            self.session.add(
                IdentityReviewCaseModel(
                    id=review_case.review_case_id,
                    tenant_id=review_case.scope.tenant_id,
                    identity_domain=review_case.scope.identity_domain,
                    source_record_id=review_case.source_record_id,
                    candidate_record_ids=list(review_case.candidate_record_ids),
                    resolution_status=review_case.resolution_status.value,
                    status=review_case.status.value,
                    opened_at=review_case.opened_at,
                    closed_at=review_case.closed_at,
                    version=1,
                )
            )
        else:
            if (
                row.tenant_id != review_case.scope.tenant_id
                or row.identity_domain != review_case.scope.identity_domain
            ):
                raise ValueError("review_case_id scope cannot change")
            row.status = review_case.status.value
            row.closed_at = review_case.closed_at
        self.session.flush()

    def get_review_case(self, review_case_id: UUID) -> ReviewCase | None:
        row = self.session.get(IdentityReviewCaseModel, review_case_id)
        if row is None:
            return None
        return ReviewCase(
            source_record_id=row.source_record_id,
            candidate_record_ids=tuple(row.candidate_record_ids),
            resolution_status=IdentityResolutionStatus(row.resolution_status),
            scope=IdentityScope(row.tenant_id, row.identity_domain),
            review_case_id=row.id,
            status=ReviewCaseStatus(row.status),
            opened_at=_required_aware(row.opened_at),
            closed_at=_optional_aware(row.closed_at),
        )

    def append_event(self, event: IdentityDecisionEvent) -> None:
        self.session.add(
            IdentityDecisionEventModel(
                id=event.event_id,
                action=event.action.value,
                reason=event.reason.value,
                actor_id=event.actor_id,
                tenant_id=event.scope.tenant_id,
                identity_domain=event.scope.identity_domain,
                source_record_id=event.source_record_id,
                master_patient_id=event.master_patient_id,
                review_case_id=event.review_case_id,
                occurred_at=event.occurred_at,
            )
        )
        self.session.flush()

    def events(self) -> tuple[IdentityDecisionEvent, ...]:
        rows = self.session.scalars(
            select(IdentityDecisionEventModel).order_by(IdentityDecisionEventModel.occurred_at)
        ).all()
        return tuple(
            IdentityDecisionEvent(
                action=IdentityDecisionAction(row.action),
                reason=IdentityDecisionReason(row.reason),
                actor_id=row.actor_id,
                scope=IdentityScope(row.tenant_id, row.identity_domain),
                source_record_id=row.source_record_id,
                event_id=row.id,
                master_patient_id=row.master_patient_id,
                review_case_id=row.review_case_id,
                occurred_at=_required_aware(row.occurred_at),
            )
            for row in rows
        )

    @staticmethod
    def _link(row: MasterPatientLinkModel) -> MasterPatientLink:
        return MasterPatientLink(
            master_patient_id=row.master_patient_id,
            source_record_id=row.source_record_id,
            source_system=row.source_system,
            scope=IdentityScope(row.tenant_id, row.identity_domain),
            status=MasterPatientLinkStatus(row.status),
            linked_at=_required_aware(row.linked_at),
            unlinked_at=_optional_aware(row.unlinked_at),
        )
