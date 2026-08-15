from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from healthcare_pipeline.canonical import CanonicalClinicalMessage
from healthcare_pipeline.clinical.models import (
    ClinicalListItem,
    ClinicalProvenance,
    ClinicalWriteResult,
    PatientClinicalSummary,
    TimelinePage,
)
from healthcare_pipeline.clinical.repository import ClinicalRepository
from healthcare_pipeline.identity.models import IdentityScope


@dataclass(slots=True)
class ClinicalMessageWriter:
    repository: ClinicalRepository

    def persist(
        self,
        *,
        message: CanonicalClinicalMessage,
        master_patient_id: UUID,
        scope: IdentityScope,
        source_system: str,
        received_at: datetime,
    ) -> ClinicalWriteResult:
        return self.repository.persist_message(
            message=message,
            master_patient_id=master_patient_id,
            scope=scope,
            source_system=source_system,
            received_at=received_at,
        )


@dataclass(slots=True)
class LongitudinalClinicalService:
    repository: ClinicalRepository

    def summary(self, *, master_patient_id: UUID, scope: IdentityScope) -> PatientClinicalSummary:
        return self.repository.summary(master_patient_id=master_patient_id, scope=scope)

    def timeline(
        self,
        *,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int = 50,
        cursor: str | None = None,
    ) -> TimelinePage:
        return self.repository.timeline(
            master_patient_id=master_patient_id,
            scope=scope,
            limit=limit,
            cursor=cursor,
        )

    def resources(
        self,
        *,
        resource_type: str,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int = 50,
    ) -> tuple[ClinicalListItem, ...]:
        return self.repository.list_resources(
            resource_type=resource_type,
            master_patient_id=master_patient_id,
            scope=scope,
            limit=limit,
        )

    def provenance(
        self,
        *,
        resource_type: str,
        resource_id: UUID,
        master_patient_id: UUID,
        scope: IdentityScope,
    ) -> ClinicalProvenance | None:
        return self.repository.provenance(
            resource_type=resource_type,
            resource_id=resource_id,
            master_patient_id=master_patient_id,
            scope=scope,
        )
