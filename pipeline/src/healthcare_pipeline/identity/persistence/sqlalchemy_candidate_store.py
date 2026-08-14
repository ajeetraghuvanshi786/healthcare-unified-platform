from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from healthcare_pipeline.identity.models import IdentityRecord, IdentityScope
from healthcare_pipeline.identity.persistence.cipher import AesGcmIdentityRecordCipher
from healthcare_pipeline.identity.store import IdentityCandidateKeyFactory, IdentityCandidateStore
from healthcare_pipeline.models.identity_master import (
    IdentityCandidateKeyModel,
    IdentitySourceRecordModel,
)


@dataclass(slots=True)
class SQLAlchemyIdentityCandidateStore(IdentityCandidateStore):
    """Durable encrypted candidate store; search indexes contain HMAC tokens, not raw PHI."""

    session: Session
    key_factory: IdentityCandidateKeyFactory
    cipher: AesGcmIdentityRecordCipher
    max_candidate_ids: int = 101

    def __post_init__(self) -> None:
        if self.max_candidate_ids < 1:
            raise ValueError("max_candidate_ids must be positive")

    def upsert(self, record: IdentityRecord) -> None:
        encrypted = self.cipher.encrypt(record)
        now = datetime.now(UTC)
        row = self.session.scalar(
            select(IdentitySourceRecordModel).where(
                IdentitySourceRecordModel.tenant_id == record.scope.tenant_id,
                IdentitySourceRecordModel.identity_domain == record.scope.identity_domain,
                IdentitySourceRecordModel.source_system == record.source_system,
                IdentitySourceRecordModel.source_record_id == record.record_id,
            )
        )
        if row is None:
            row = IdentitySourceRecordModel(
                tenant_id=record.scope.tenant_id,
                identity_domain=record.scope.identity_domain,
                source_system=record.source_system,
                source_record_id=record.record_id,
                encryption_key_id=encrypted.key_id,
                nonce=encrypted.nonce,
                ciphertext=encrypted.ciphertext,
                created_at=now,
                updated_at=now,
            )
            self.session.add(row)
            self.session.flush()
        else:
            row.encryption_key_id = encrypted.key_id
            row.nonce = encrypted.nonce
            row.ciphertext = encrypted.ciphertext
            row.updated_at = now
            self.session.flush()
            self.session.execute(
                delete(IdentityCandidateKeyModel).where(
                    IdentityCandidateKeyModel.source_record_db_id == row.id
                )
            )

        for key_hash in self.key_factory.keys(record):
            self.session.add(
                IdentityCandidateKeyModel(
                    source_record_db_id=row.id,
                    tenant_id=record.scope.tenant_id,
                    identity_domain=record.scope.identity_domain,
                    key_hash=key_hash,
                )
            )
        self.session.flush()

    def get(self, record_id: str) -> IdentityRecord | None:
        normalized = record_id.strip()
        if not normalized:
            raise ValueError("record_id must not be blank")
        rows = self.session.scalars(
            select(IdentitySourceRecordModel).where(
                IdentitySourceRecordModel.source_record_id == normalized
            ).limit(2)
        ).all()
        if not rows:
            return None
        if len(rows) > 1:
            raise ValueError("record_id is not globally unique")
        row = rows[0]
        if row.encryption_key_id != self.cipher.key_id:
            raise RuntimeError(
                "stored identity record requires an unavailable encryption key version"
            )
        return self.cipher.decrypt(
            record_id=row.source_record_id,
            source_system=row.source_system,
            scope=IdentityScope(row.tenant_id, row.identity_domain),
            nonce=row.nonce,
            ciphertext=row.ciphertext,
        )

    def candidate_ids(self, record: IdentityRecord) -> tuple[str, ...]:
        keys = self.key_factory.keys(record)
        if not keys:
            return ()
        rows = self.session.execute(
            select(IdentitySourceRecordModel.source_record_id)
            .join(
                IdentityCandidateKeyModel,
                IdentityCandidateKeyModel.source_record_db_id == IdentitySourceRecordModel.id,
            )
            .where(
                IdentityCandidateKeyModel.tenant_id == record.scope.tenant_id,
                IdentityCandidateKeyModel.identity_domain == record.scope.identity_domain,
                IdentityCandidateKeyModel.key_hash.in_(keys),
                IdentitySourceRecordModel.source_record_id != record.record_id,
            )
            .distinct()
            .order_by(IdentitySourceRecordModel.source_record_id)
            .limit(self.max_candidate_ids)
        ).scalars()
        return tuple(rows)
