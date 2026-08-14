from __future__ import annotations

import os
from uuid import uuid4

import httpx

from healthcare_pipeline.config.settings import get_settings


def main() -> None:
    settings = get_settings()
    token = settings.require_api_auth_token()
    base_url = os.getenv(
        "HEALTHCARE_API_BASE_URL",
        f"http://{settings.api_host}:{settings.api_port}",
    ).rstrip("/")

    unique = uuid4().hex[:12]
    hl7 = (
        "MSH|^~\\&|LOCAL|HOSPITAL|HUP|PLATFORM|202608112030||ADT^A01|"
        f"MSG-{unique}|P|2.5\r"
        f"PID|1||MRN-{unique}^^^LOCAL^MR||DOE^SYNTHETIC||19900101|F\r"
        "PV1|1|I|WARD^101^A^HOSPITAL\r"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "local-test",
        "X-Identity-Domain": "local-enterprise",
        "X-Actor-ID": "local-e2e",
    }

    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        live = client.get("/health/live")
        live.raise_for_status()

        ready = client.get("/health/ready")
        if ready.status_code != 200:
            raise SystemExit(
                "Database is not ready; start PostgreSQL and apply migrations first"
            )

        result = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "local-synthetic", "hl7": hl7},
        )
        result.raise_for_status()
        body = result.json()

        master_id = body.get("master_patient_id")
        if not master_id:
            raise SystemExit(f"Expected a master patient, got: {body}")

        master = client.get(f"/api/v1/master-patients/{master_id}", headers=headers)
        master.raise_for_status()
        master_body = master.json()

    if master_body.get("master_patient_id") != master_id:
        raise SystemExit("Master-patient read-back did not match the processing response")

    print("Local network E2E passed")
    print(f"source_message_id={body['source_message_id']}")
    print(f"identity_status={body['identity_status']}")
    print(f"master_patient_id={master_id}")


if __name__ == "__main__":
    main()
