from healthcare_pipeline.application.processing import (
    HealthcareMessageProcessingService,
    ProcessingStatus,
)
from healthcare_pipeline.identity import (
    HmacIdentityKeyEncoder,
    IdentityResolutionStatus,
    IdentityScope,
    InMemoryIdentityCandidateStore,
    InMemoryMasterIdentityRepository,
    PatientIdentityService,
)


def _adt_message() -> bytes:
    fields = [""] * 20
    fields[0] = "PV1"
    fields[1] = "1"
    fields[2] = "I"
    fields[3] = "ICU^101^A^HOSPITAL"
    fields[7] = "111^SMITH^JOHN"
    fields[19] = "V100^^^HOSPITAL^VN"
    return (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HIE|202608071030-0400||"
        "ADT^A01|MSG-100|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||DOE^JANE||19900115|F|||"
        "1 MAIN ST^^BOSTON^MA^02110^USA||5551234\r"
        + "|".join(fields)
    ).encode()


def test_processing_status_is_stable_contract() -> None:
    assert ProcessingStatus.PROCESSED.value == "processed"
    assert ProcessingStatus.REJECTED.value == "rejected"


def test_application_service_processes_hl7_and_creates_master_identity() -> None:
    encoder = HmacIdentityKeyEncoder(b"k" * 32)
    candidate_store = InMemoryIdentityCandidateStore(encoder)
    master_repository = InMemoryMasterIdentityRepository()
    service = HealthcareMessageProcessingService(
        identity=PatientIdentityService.create(candidate_store),
        master_repository=master_repository,
        record_id_encoder=encoder,
        max_payload_bytes=1_000_000,
    )

    outcome = service.process_hl7(
        _adt_message(),
        source_system="epic",
        scope=IdentityScope("tenant-a", "enterprise"),
        actor_id="system",
    )

    assert outcome.status is ProcessingStatus.PROCESSED
    assert outcome.identity_status is IdentityResolutionStatus.NO_MATCH
    assert outcome.master_patient_id is not None
    assert outcome.source_record_id is not None
    links = master_repository.active_links_for_master(outcome.master_patient_id)
    assert len(links) == 1
    assert links[0].source_record_id == outcome.source_record_id
