from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from healthcare_pipeline.canonical import CanonicalClinicalMessage
from healthcare_pipeline.clinical.models import (
    ClinicalListItem,
    ClinicalProvenance,
    ClinicalWriteResult,
    PatientClinicalSummary,
    TimelinePage,
)
from healthcare_pipeline.identity.models import IdentityScope


class ClinicalRepository(Protocol):
    def persist_message(
        self,
        *,
        message: CanonicalClinicalMessage,
        master_patient_id: UUID,
        scope: IdentityScope,
        source_system: str,
        received_at: datetime,
    ) -> ClinicalWriteResult: ...

    def summary(
        self,
        *,
        master_patient_id: UUID,
        scope: IdentityScope,
    ) -> PatientClinicalSummary: ...

    def timeline(
        self,
        *,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int,
        cursor: str | None,
    ) -> TimelinePage: ...

    def list_resources(
        self,
        *,
        resource_type: str,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int,
    ) -> tuple[ClinicalListItem, ...]: ...

    def provenance(
        self,
        *,
        resource_type: str,
        resource_id: UUID,
        master_patient_id: UUID,
        scope: IdentityScope,
    ) -> ClinicalProvenance | None: ...
