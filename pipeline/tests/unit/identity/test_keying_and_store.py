from healthcare_pipeline.canonical import HumanName, Identifier, Patient
from healthcare_pipeline.identity import (
    HmacIdentityKeyEncoder,
    IdentityRecord,
    IdentityScope,
    InMemoryIdentityCandidateStore,
)


def _record(record_id: str, tenant: str = "tenant-a") -> IdentityRecord:
    return IdentityRecord(
        record_id=record_id,
        source_system="ehr-a",
        scope=IdentityScope(tenant, "enterprise-patient"),
        patient=Patient(
            identifiers=(Identifier("12345", system="HOSP-A", type_code="MR"),),
            names=(HumanName(family="Doe", given=("Jane",)),),
        ),
    )


def test_hmac_encoder_is_deterministic_and_does_not_expose_source_value() -> None:
    encoder = HmacIdentityKeyEncoder(b"x" * 32)
    first = encoder.encode("identifier", "MRN-123")
    second = encoder.encode("identifier", "MRN-123")

    assert first == second
    assert "MRN-123" not in first
    assert len(first) == 64


def test_candidate_store_isolated_by_identity_scope() -> None:
    store = InMemoryIdentityCandidateStore(HmacIdentityKeyEncoder(b"x" * 32))
    store.upsert(_record("a", "tenant-a"))
    store.upsert(_record("b", "tenant-b"))

    query = _record("q", "tenant-a")
    assert store.candidate_ids(query) == ("a",)


def test_store_upsert_replaces_old_index_keys() -> None:
    store = InMemoryIdentityCandidateStore(HmacIdentityKeyEncoder(b"x" * 32))
    old = _record("a")
    store.upsert(old)
    changed = IdentityRecord(
        record_id="a",
        source_system="ehr-a",
        scope=old.scope,
        patient=Patient(
            identifiers=(Identifier("99999", system="HOSP-A", type_code="MR"),),
            names=old.patient.names,
        ),
    )
    store.upsert(changed)

    assert store.candidate_ids(_record("query")) == ()
