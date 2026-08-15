from __future__ import annotations

import secrets

import httpx

from healthcare_pipeline.config.settings import get_settings


def main() -> None:
    settings = get_settings()
    base_url = f"http://{settings.api_host}:{settings.api_port}"
    token = settings.require_api_auth_token()
    suffix = secrets.token_hex(6)
    message_id = f"P4-{suffix}"
    patient_id = f"PAT-{suffix}"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "local-phase4",
        "X-Identity-Domain": "enterprise",
        "X-Actor-ID": "phase4-e2e",
    }
    hl7 = (
        "MSH|^~\\&|EPIC|HOSPITAL|HIE|HIE|202608141200-0400||"
        f"ADT^A01|{message_id}|P|2.5\r"
        f"PID|1||{patient_id}^^^HOSPITAL^MR||DOE^JANE||19900115|F\r"
        "PV1|1|I|ICU^101^A^HOSPITAL||||||||||||||||V123|||||||||||||||||||||||||"
        "202608141100-0400\r"
        "DG1|1||I10^Essential hypertension^ICD10|Essential hypertension|"
        "202608141200-0400|F\r"
        "AL1|1|DA^Drug allergy^HL70127|PEN^Penicillin^LOCAL|"
        "MO^Moderate^HL70128|RASH|20260801"
    )

    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        live = client.get("/health/live")
        live.raise_for_status()
        ready = client.get("/health/ready")
        ready.raise_for_status()

        created = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "phase4-synthetic", "hl7": hl7},
        )
        created.raise_for_status()
        body = created.json()
        if body["clinical_write_status"] != "created":
            raise RuntimeError(f"expected created clinical write, got {body!r}")
        master_patient_id = body["master_patient_id"]
        if not master_patient_id:
            raise RuntimeError("E2E processing did not return a master patient")

        repeated = client.post(
            "/api/v1/hl7/process",
            headers=headers,
            json={"source_system": "phase4-synthetic", "hl7": hl7},
        )
        repeated.raise_for_status()
        if repeated.json()["clinical_write_status"] != "already_processed":
            raise RuntimeError("replayed source message was not idempotent")

        summary = client.get(
            f"/api/v1/master-patients/{master_patient_id}/clinical-summary",
            headers=headers,
        )
        summary.raise_for_status()
        counts = summary.json()
        for field in ("encounter_count", "diagnosis_count", "allergy_count"):
            if counts[field] < 1:
                raise RuntimeError(f"expected {field} to be at least 1: {counts!r}")

        timeline = client.get(
            f"/api/v1/master-patients/{master_patient_id}/timeline?limit=10",
            headers=headers,
        )
        timeline.raise_for_status()
        if len(timeline.json()["items"]) < 3:
            raise RuntimeError("timeline did not contain expected clinical events")

        encounters = client.get(
            f"/api/v1/master-patients/{master_patient_id}/clinical/encounters",
            headers=headers,
        )
        encounters.raise_for_status()
        encounter_id = encounters.json()["items"][0]["resource_id"]

        provenance = client.get(
            f"/api/v1/master-patients/{master_patient_id}/clinical/"
            f"encounters/{encounter_id}/provenance",
            headers=headers,
        )
        provenance.raise_for_status()
        if provenance.json()["source_message_id"] != message_id:
            raise RuntimeError("clinical provenance did not preserve source lineage")

    print("Phase 4A-4F local network E2E passed")
    print(f"source_message_id={message_id}")
    print(f"master_patient_id={master_patient_id}")
    print(f"clinical_message_id={body['clinical_message_id']}")
    print("idempotency=verified")
    print("summary=verified")
    print("timeline=verified")
    print("provenance=verified")


if __name__ == "__main__":
    main()
