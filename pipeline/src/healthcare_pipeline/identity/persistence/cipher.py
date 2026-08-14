from __future__ import annotations

import os
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from healthcare_pipeline.identity.models import IdentityRecord, IdentityScope
from healthcare_pipeline.identity.persistence.serializer import PatientIdentitySnapshotSerializer


@dataclass(frozen=True, slots=True)
class EncryptedIdentityRecord:
    key_id: str
    nonce: bytes
    ciphertext: bytes


@dataclass(frozen=True, slots=True)
class AesGcmIdentityRecordCipher:
    """AES-256-GCM envelope for PHI-bearing identity snapshots with bound record metadata."""

    key: bytes
    key_id: str = "local-v1"
    serializer: PatientIdentitySnapshotSerializer = field(
        default_factory=PatientIdentitySnapshotSerializer
    )

    def __post_init__(self) -> None:
        if not isinstance(self.key, bytes) or len(self.key) != 32:
            raise ValueError("identity encryption key must contain exactly 32 bytes")
        if not isinstance(self.key_id, str) or not self.key_id.strip():
            raise ValueError("key_id must be a non-blank string")

    def encrypt(self, record: IdentityRecord) -> EncryptedIdentityRecord:
        plaintext = self.serializer.dumps(record.patient)
        nonce = os.urandom(12)
        ciphertext = AESGCM(self.key).encrypt(nonce, plaintext, self._aad(record))
        return EncryptedIdentityRecord(self.key_id.strip(), nonce, ciphertext)

    def decrypt(
        self,
        *,
        record_id: str,
        source_system: str,
        scope: IdentityScope,
        nonce: bytes,
        ciphertext: bytes,
    ) -> IdentityRecord:
        record = IdentityRecord(
            record_id=record_id,
            source_system=source_system,
            scope=scope,
            patient=self.serializer.loads(
                AESGCM(self.key).decrypt(
                    nonce,
                    ciphertext,
                    self._aad_values(record_id, source_system, scope),
                )
            ),
        )
        return record

    def _aad(self, record: IdentityRecord) -> bytes:
        return self._aad_values(record.record_id, record.source_system, record.scope)

    @staticmethod
    def _aad_values(record_id: str, source_system: str, scope: IdentityScope) -> bytes:
        return (
            f"{scope.tenant_id}\x1f{scope.identity_domain}\x1f"
            f"{source_system}\x1f{record_id}"
        ).encode()
