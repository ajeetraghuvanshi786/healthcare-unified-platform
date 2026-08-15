from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from healthcare_pipeline.canonical import CanonicalClinicalMessage, Coding, Diagnosis
from healthcare_pipeline.clinical import LongitudinalClinicalService, SQLAlchemyClinicalRepository
from healthcare_pipeline.identity.models import IdentityScope
from healthcare_pipeline.models.clinical import (
    ClinicalAllergyRecord,
    ClinicalCoverageRecord,
    ClinicalDiagnosisRecord,
    ClinicalEncounterRecord,
    ClinicalMedicationAdministrationRecord,
    ClinicalMedicationOrderRecord,
    ClinicalMessageRecord,
    ClinicalObservationRecord,
    ClinicalProvenanceRecord,
    ClinicalTimelineEventRecord,
)
from healthcare_pipeline.models.identity_master import MasterPatientModel


def test_summary_and_timeline_are_scope_isolated_and_cursor_paginated() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in (
        MasterPatientModel.__table__,
        ClinicalMessageRecord.__table__,
        ClinicalEncounterRecord.__table__,
        ClinicalDiagnosisRecord.__table__,
        ClinicalObservationRecord.__table__,
        ClinicalAllergyRecord.__table__,
        ClinicalMedicationOrderRecord.__table__,
        ClinicalMedicationAdministrationRecord.__table__,
        ClinicalCoverageRecord.__table__,
        ClinicalProvenanceRecord.__table__,
        ClinicalTimelineEventRecord.__table__,
    ):
        table.create(engine)

    scope = IdentityScope("tenant-a", "enterprise")
    master_id = uuid4()
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.add(
            MasterPatientModel(
                id=master_id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        repository = SQLAlchemyClinicalRepository(session)
        for index in range(3):
            message = CanonicalClinicalMessage(
                source_format="hl7_v2",
                source_message_id=f"MSG-{index}",
                source_event_code="ORU^R01",
                diagnoses=(
                    Diagnosis(
                        code=Coding(code=f"D{index}", display=f"Diagnosis {index}"),
                        recorded_datetime=datetime(2026, 8, 14, 10 + index, tzinfo=UTC),
                    ),
                ),
            )
            repository.persist_message(
                message=message,
                master_patient_id=master_id,
                scope=scope,
                source_system="hospital-a",
                received_at=datetime(2026, 8, 14, 10 + index, tzinfo=UTC),
            )

        service = LongitudinalClinicalService(repository)
        summary = service.summary(master_patient_id=master_id, scope=scope)
        assert summary.diagnosis_count == 3
        assert summary.encounter_count == 0

        first = service.timeline(master_patient_id=master_id, scope=scope, limit=2)
        assert len(first.items) == 2
        assert first.next_cursor is not None
        second = service.timeline(
            master_patient_id=master_id,
            scope=scope,
            limit=2,
            cursor=first.next_cursor,
        )
        assert len(second.items) == 1
        assert {item.resource_id for item in first.items}.isdisjoint(
            {item.resource_id for item in second.items}
        )
