from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from healthcare_pipeline.canonical import (
    Allergy,
    CanonicalClinicalMessage,
    Coding,
    Coverage,
    Diagnosis,
    Encounter,
    EncounterClass,
    MedicationAdministration,
    MedicationOrder,
    Observation,
    ObservationOrder,
    Period,
    Quantity,
)
from healthcare_pipeline.clinical import (
    ClinicalMessageConflict,
    ClinicalWriteStatus,
    SQLAlchemyClinicalRepository,
)
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


def _create_tables(engine: object) -> None:
    tables = [
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
    ]
    for table in tables:
        table.create(engine)  # type: ignore[arg-type]


def _message(message_id: str = "MSG-1") -> CanonicalClinicalMessage:
    return CanonicalClinicalMessage(
        source_format="hl7_v2",
        source_message_id=message_id,
        source_event_code="ADT^A01",
        encounter=Encounter(
            encounter_class=EncounterClass.INPATIENT,
            period=Period(
                start=datetime(2026, 8, 14, 10, tzinfo=UTC),
                end=datetime(2026, 8, 14, 12, tzinfo=UTC),
            ),
        ),
        diagnoses=(
            Diagnosis(
                code=Coding(code="I10", display="Hypertension", system="ICD-10"),
                recorded_datetime=datetime(2026, 8, 14, 11, tzinfo=UTC),
            ),
        ),
        allergies=(
            Allergy(
                allergen=Coding(code="PEN", display="Penicillin", system="LOCAL"),
                reactions=("rash",),
                identified_date=date(2026, 8, 1),
            ),
        ),
        observation_orders=(
            ObservationOrder(
                service=Coding(code="LAB", display="Laboratory"),
                observation_datetime=datetime(2026, 8, 14, 11, 30, tzinfo=UTC),
                results=(
                    Observation(
                        code=Coding(code="718-7", display="Hemoglobin", system="LOINC"),
                        values=("13.8",),
                        status="F",
                        value_type="NM",
                        effective_datetime=datetime(2026, 8, 14, 11, 30, tzinfo=UTC),
                    ),
                ),
            ),
        ),
        medication_orders=(
            MedicationOrder(
                medication=Coding(code="MED-1", display="Example medicine"),
                status="active",
            ),
        ),
        medication_administrations=(
            MedicationAdministration(
                medication=Coding(code="MED-1", display="Example medicine"),
                amount=Quantity(Decimal("1")),
                start_datetime=datetime(2026, 8, 14, 11, 45, tzinfo=UTC),
                status="completed",
            ),
        ),
        coverages=(Coverage(payer_name="Example Health", group_number="G-1"),),
    )


def _seed_master(session: Session, master_id: object) -> None:
    now = datetime.now(UTC)
    session.add(
        MasterPatientModel(
            id=master_id,
            tenant_id="tenant-a",
            identity_domain="enterprise",
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()


def test_persist_message_is_idempotent_and_writes_provenance_and_timeline() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    _create_tables(engine)
    scope = IdentityScope("tenant-a", "enterprise")
    master_id = uuid4()

    with Session(engine) as session:
        _seed_master(session, master_id)
        repository = SQLAlchemyClinicalRepository(session)
        first = repository.persist_message(
            message=_message(),
            master_patient_id=master_id,
            scope=scope,
            source_system="hospital-a",
            received_at=datetime(2026, 8, 14, 12, 30, tzinfo=UTC),
        )
        second = repository.persist_message(
            message=_message(),
            master_patient_id=master_id,
            scope=scope,
            source_system="hospital-a",
            received_at=datetime(2026, 8, 14, 12, 31, tzinfo=UTC),
        )

        assert first.status is ClinicalWriteStatus.CREATED
        assert second.status is ClinicalWriteStatus.ALREADY_PROCESSED
        assert second.clinical_message_id == first.clinical_message_id
        assert session.scalar(select(func.count()).select_from(ClinicalMessageRecord)) == 1
        assert session.scalar(select(func.count()).select_from(ClinicalProvenanceRecord)) == 7
        assert session.scalar(select(func.count()).select_from(ClinicalTimelineEventRecord)) == 7
        encounter = session.scalar(select(ClinicalEncounterRecord))
        coverage = session.scalar(select(ClinicalCoverageRecord))
        assert encounter is not None
        assert coverage is not None
        assert "identifiers" not in encounter.snapshot
        assert "subscriber_names" not in coverage.snapshot
        assert "subscriber_identifiers" not in coverage.snapshot


def test_same_source_message_with_different_content_is_rejected() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    _create_tables(engine)
    scope = IdentityScope("tenant-a", "enterprise")
    master_id = uuid4()

    with Session(engine) as session:
        _seed_master(session, master_id)
        repository = SQLAlchemyClinicalRepository(session)
        repository.persist_message(
            message=_message(),
            master_patient_id=master_id,
            scope=scope,
            source_system="hospital-a",
            received_at=datetime.now(UTC),
        )
        changed = CanonicalClinicalMessage(
            source_format="hl7_v2",
            source_message_id="MSG-1",
            source_event_code="ADT^A03",
        )
        with pytest.raises(ClinicalMessageConflict):
            repository.persist_message(
                message=changed,
                master_patient_id=master_id,
                scope=scope,
                source_system="hospital-a",
                received_at=datetime.now(UTC),
            )
