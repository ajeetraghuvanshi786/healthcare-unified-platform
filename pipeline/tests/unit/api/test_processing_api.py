from pathlib import Path

from fastapi.testclient import TestClient

from healthcare_pipeline.api.main import create_app
from healthcare_pipeline.config.database import create_database_engine
from healthcare_pipeline.config.settings import Settings
from healthcare_pipeline.models.identity_master import (
    IdentityCandidateKeyModel,
    IdentityDecisionEventModel,
    IdentityReviewCaseModel,
    IdentitySourceRecordModel,
    MasterPatientLinkModel,
    MasterPatientModel,
)


def _create_identity_tables(database_url: str) -> None:
    engine = create_database_engine(database_url)
    for table in (
        MasterPatientModel.__table__,
        IdentityReviewCaseModel.__table__,
        MasterPatientLinkModel.__table__,
        IdentityDecisionEventModel.__table__,
        IdentitySourceRecordModel.__table__,
        IdentityCandidateKeyModel.__table__,
    ):
        table.create(engine)
    engine.dispose()


def test_protected_api_processes_hl7_and_reads_master_patient(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'identity.db'}"
    _create_identity_tables(database_url)
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
