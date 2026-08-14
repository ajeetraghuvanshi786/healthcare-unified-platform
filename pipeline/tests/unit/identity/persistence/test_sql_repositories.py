from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import (
    HmacIdentityKeyEncoder,
    IdentityCandidateKeyFactory,
    IdentityRecord,
    IdentityScope,
    MasterPatient,
    MasterPatientLink,
)
from healthcare_pipeline.identity.master.sqlalchemy_repository import (
    SQLAlchemyMasterIdentityRepository,
)
from healthcare_pipeline.identity.persistence import (
    AesGcmIdentityRecordCipher,
    SQLAlchemyIdentityCandidateStore,
)
from healthcare_pipeline.models.identity_master import (
    IdentityCandidateKeyModel,
    IdentityDecisionEventModel,
    IdentityReviewCaseModel,
    IdentitySourceRecordModel,
    MasterPatientLinkModel,
    MasterPatientModel,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in (
        MasterPatientModel.__table__,
        IdentityReviewCaseModel.__table__,
        MasterPatientLinkModel.__table__,
        IdentityDecisionEventModel.__table__,
        IdentitySourceRecordModel.__table__,
        IdentityCandidateKeyModel.__table__,
    ):
        table.create(engine)
    return Session(engine)


def _record(record_id: str, mrn: str) -> IdentityRecord:
    return IdentityRecord(
        record_id=record_id,
        source_system="epic",
        scope=IdentityScope("tenant-a", "enterprise"),
        patient=Patient(
            identifiers=(Identifier(mrn, system="hospital-a"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
        ),
    )


def test_sql_candidate_store_persists_encrypted_record_and_finds_candidate() -> None:
    session = _session()
    encoder = HmacIdentityKeyEncoder(b"k" * 32)
    store = SQLAlchemyIdentityCandidateStore(
        session,
        IdentityCandidateKeyFactory(encoder),
        AesGcmIdentityRecordCipher(b"e" * 32),
    )
    first = _record("record-1", "MRN-1")
    second = _record("record-2", "MRN-1")
    store.upsert(first)
    assert store.get("record-1") == first
    assert store.candidate_ids(second) == ("record-1",)


def test_sql_master_repository_round_trip() -> None:
    session = _session()
    repository = SQLAlchemyMasterIdentityRepository(session)
    scope = IdentityScope("tenant-a", "enterprise")
    master = MasterPatient(scope=scope, created_at=datetime.now(UTC))
    repository.create_master(master)
    repository.save_link(
        MasterPatientLink(
            master_patient_id=master.master_patient_id,
            source_record_id="record-1",
            source_system="epic",
            scope=scope,
        )
    )
    restored = repository.get_master(master.master_patient_id)
    assert restored is not None
    assert restored.master_patient_id == master.master_patient_id
    assert len(repository.active_links_for_master(master.master_patient_id)) == 1


def test_sql_candidate_store_rejects_unknown_encryption_key_version() -> None:
    session = _session()
    encoder = HmacIdentityKeyEncoder(b"k" * 32)
    writer = SQLAlchemyIdentityCandidateStore(
        session,
        IdentityCandidateKeyFactory(encoder),
        AesGcmIdentityRecordCipher(b"e" * 32, key_id="key-v1"),
    )
    writer.upsert(_record("record-1", "MRN-1"))

    reader = SQLAlchemyIdentityCandidateStore(
        session,
        IdentityCandidateKeyFactory(encoder),
        AesGcmIdentityRecordCipher(b"f" * 32, key_id="key-v2"),
    )
    with pytest.raises(RuntimeError, match="encryption key version"):
        reader.get("record-1")


def test_sql_master_repository_rejects_master_scope_reuse() -> None:
    session = _session()
    repository = SQLAlchemyMasterIdentityRepository(session)
    original = MasterPatient(scope=IdentityScope("tenant-a", "enterprise"))
    repository.create_master(original)

    conflicting = MasterPatient(
        scope=IdentityScope("tenant-b", "enterprise"),
        master_patient_id=original.master_patient_id,
    )
    with pytest.raises(ValueError, match="different identity scope"):
        repository.create_master(conflicting)
