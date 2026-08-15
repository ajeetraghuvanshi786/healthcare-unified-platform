from pathlib import Path

from fastapi.testclient import TestClient

from healthcare_pipeline.api.main import create_app
from healthcare_pipeline.config.database import create_database_engine
from healthcare_pipeline.config.settings import Settings
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
from healthcare_pipeline.models.identity_master import (
    IdentityCandidateKeyModel,
    IdentityDecisionEventModel,
    IdentityReviewCaseModel,
    IdentitySourceRecordModel,
    MasterPatientLinkModel,
    MasterPatientModel,
)


def _create_application_tables(database_url: str) -> None:
    engine = create_database_engine(database_url)
    for table in (
        MasterPatientModel.__table__,
        IdentityReviewCaseModel.__table__,
        MasterPatientLinkModel.__table__,
        IdentityDecisionEventModel.__table__,
        IdentitySourceRecordModel.__table__,
        IdentityCandidateKeyModel.__table__,
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
    engine.dispose()


def test_protected_api_processes_hl7_and_reads_master_patient(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'identity.db'}"
    _create_application_tables(database_url)
    settings = Settings(
        database_url=database_url,
        api_auth_token="a" * 48,
        identity_hmac_secret="h" * 48,
        identity_encryption_key_hex="11" * 32,
        _env_file=None,
    )
    app = create_app(settings)
    headers = {
        "Authorization": f"Bearer {'a' * 48}",
        "X-Tenant-ID": "tenant-a",
        "X-Identity-Domain": "enterprise",
        "X-Actor-ID": "test-runner",
    }
    hl7 = (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HIE|202608071030-0400||"
        "ADT^A01|API-MSG-1|P|2.5\r"
        "PID|1||12345^^^HOSPITAL^MR||DOE^JANE||19900115|F\r"
        "PV1|1|I|ICU^101^A^HOSPITAL"
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "epic", "hl7": hl7},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "processed"
        assert body["identity_status"] == "no_match"
        assert body["master_patient_id"] is not None
        assert body["clinical_message_id"] is not None
        assert body["clinical_write_status"] == "created"

        summary = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}/clinical-summary",
            headers=headers,
        )
        assert summary.status_code == 200
        assert summary.json()["encounter_count"] == 1

        timeline = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}/timeline",
            headers=headers,
        )
        assert timeline.status_code == 200
        assert len(timeline.json()["items"]) == 1
        assert timeline.json()["items"][0]["event_type"] == "encounter"

        encounters = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}/clinical/encounters",
            headers=headers,
        )
        assert encounters.status_code == 200
        encounter_id = encounters.json()["items"][0]["resource_id"]
        provenance = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}/clinical/"
            f"encounters/{encounter_id}/provenance",
            headers=headers,
        )
        assert provenance.status_code == 200
        assert provenance.json()["source_system"] == "epic"
        assert provenance.json()["source_message_id"] == "API-MSG-1"

        wrong_scope_headers = dict(headers)
        wrong_scope_headers["X-Tenant-ID"] = "tenant-b"
        hidden = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}/clinical-summary",
            headers=wrong_scope_headers,
        )
        assert hidden.status_code == 404

        repeated = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "epic", "hl7": hl7},
        )
        assert repeated.status_code == 200
        assert repeated.json()["clinical_write_status"] == "already_processed"
        assert repeated.json()["clinical_message_id"] == body["clinical_message_id"]

        changed_hl7 = hl7.replace("ADT^A01", "ADT^A03")
        conflict = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "epic", "hl7": changed_hl7},
        )
        assert conflict.status_code == 409

        master = client.get(
            f"/api/v1/master-patients/{body['master_patient_id']}",
            headers=headers,
        )
        assert master.status_code == 200
        assert master.json()["tenant_id"] == "tenant-a"
        assert len(master.json()["links"]) == 1


def test_protected_api_rejects_missing_bearer_token() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        api_auth_token="a" * 48,
        identity_hmac_secret="h" * 48,
        identity_encryption_key_hex="11" * 32,
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/hl7/process",
            headers={
                "X-Tenant-ID": "tenant-a",
                "X-Identity-Domain": "enterprise",
                "X-Actor-ID": "test-runner",
            },
            json={"source_system": "epic", "hl7": "MSH|^~\\&"},
        )
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_protected_api_rejects_oversized_identity_context() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        api_auth_token="a" * 48,
        identity_hmac_secret="h" * 48,
        identity_encryption_key_hex="11" * 32,
        _env_file=None,
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/hl7/process",
            headers={
                "Authorization": f"Bearer {'a' * 48}",
                "X-Tenant-ID": "t" * 129,
                "X-Identity-Domain": "enterprise",
                "X-Actor-ID": "test-runner",
            },
            json={"source_system": "epic", "hl7": "MSH|^~\\&"},
        )
    assert response.status_code == 400
