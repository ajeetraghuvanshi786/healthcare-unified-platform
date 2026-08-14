from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from healthcare_pipeline.application.identity_review import IdentityReviewApplicationService
from healthcare_pipeline.application.processing import HealthcareMessageProcessingService
from healthcare_pipeline.config.settings import Settings
from healthcare_pipeline.identity.keying import HmacIdentityKeyEncoder
from healthcare_pipeline.identity.master.sqlalchemy_repository import (
    SQLAlchemyMasterIdentityRepository,
)
from healthcare_pipeline.identity.persistence import (
    AesGcmIdentityRecordCipher,
    SQLAlchemyIdentityCandidateStore,
)
from healthcare_pipeline.identity.service import PatientIdentityService
from healthcare_pipeline.identity.store import IdentityCandidateKeyFactory


@dataclass(frozen=True, slots=True)
class ApplicationRuntime:
    """Build transaction-scoped application services from process configuration."""

    settings: Settings

    def processing_service(self, session: Session) -> HealthcareMessageProcessingService:
        encoder, candidate_store = self._identity_store(session)
        identity = PatientIdentityService.create(
            candidate_store,
            max_candidates=self.settings.identity_max_candidates,
        )
        return HealthcareMessageProcessingService(
            identity=identity,
            master_repository=SQLAlchemyMasterIdentityRepository(session),
            record_id_encoder=encoder,
            max_payload_bytes=self.settings.max_hl7_payload_bytes,
        )

    def identity_review_service(self, session: Session) -> IdentityReviewApplicationService:
        _, candidate_store = self._identity_store(session)
        return IdentityReviewApplicationService(
            candidate_store=candidate_store,
            master_repository=SQLAlchemyMasterIdentityRepository(session),
        )

    def _identity_store(
        self,
        session: Session,
    ) -> tuple[HmacIdentityKeyEncoder, SQLAlchemyIdentityCandidateStore]:
        encoder = HmacIdentityKeyEncoder(self.settings.require_identity_hmac_secret())
        key_factory = IdentityCandidateKeyFactory(encoder)
        cipher = AesGcmIdentityRecordCipher(
            key=self.settings.require_identity_encryption_key(),
            key_id=self.settings.identity_encryption_key_id,
        )
        store = SQLAlchemyIdentityCandidateStore(
            session=session,
            key_factory=key_factory,
            cipher=cipher,
            max_candidate_ids=self.settings.identity_max_candidates + 1,
        )
        return encoder, store
