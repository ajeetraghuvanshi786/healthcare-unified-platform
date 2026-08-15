from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from healthcare_pipeline.clinical.models import ClinicalWriteStatus
from healthcare_pipeline.clinical.service import ClinicalMessageWriter
from healthcare_pipeline.identity.keying import IdentityKeyEncoder
from healthcare_pipeline.identity.master.models import IdentityDecisionReason
from healthcare_pipeline.identity.master.repository import MasterIdentityRepository
from healthcare_pipeline.identity.master.service import MasterPatientIdentityService
from healthcare_pipeline.identity.models import (
    IdentityRecord,
    IdentityResolutionStatus,
    IdentityScope,
)
from healthcare_pipeline.identity.service import PatientIdentityService
from healthcare_pipeline.parsers.hl7 import HL7ClinicalMessageAssembler, HL7Parser
from healthcare_pipeline.terminology.canonical import CanonicalTerminologyService
from healthcare_pipeline.transformers.hl7_to_canonical import HL7ToCanonicalTransformer
from healthcare_pipeline.validators.canonical.validator import CanonicalValidator


class ProcessingStatus(StrEnum):
    PROCESSED = "processed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ProcessingOutcome:
    status: ProcessingStatus
    source_message_id: str
    source_event_code: str
    validation_error_count: int
    validation_warning_count: int
    terminology_status_counts: tuple[tuple[str, int], ...]
    identity_status: IdentityResolutionStatus | None = None
    source_record_id: str | None = None
    master_patient_id: UUID | None = None
    review_case_id: UUID | None = None
    clinical_message_id: UUID | None = None
    clinical_write_status: ClinicalWriteStatus | None = None


@dataclass(slots=True)
class HealthcareMessageProcessingService:
    """Orchestrate validated HL7, identity resolution and durable clinical writes."""

    identity: PatientIdentityService
    master_repository: MasterIdentityRepository
    record_id_encoder: IdentityKeyEncoder
    max_payload_bytes: int
    clinical_writer: ClinicalMessageWriter | None = None
    parser: HL7Parser = field(default_factory=HL7Parser)
    assembler: HL7ClinicalMessageAssembler = field(default_factory=HL7ClinicalMessageAssembler)
    transformer: HL7ToCanonicalTransformer = field(default_factory=HL7ToCanonicalTransformer)
    validator: CanonicalValidator = field(default_factory=CanonicalValidator)
    terminology: CanonicalTerminologyService = field(default_factory=CanonicalTerminologyService)

    def process_hl7(
        self,
        payload: bytes,
        *,
        source_system: str,
        scope: IdentityScope,
        actor_id: str,
    ) -> ProcessingOutcome:
        received_at = datetime.now(UTC)
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("payload must be non-empty bytes")
        if len(payload) > self.max_payload_bytes:
            raise ValueError("HL7 payload exceeds configured size limit")

        structural = self.parser.parse_message(payload)
        semantic = self.assembler.assemble(structural)
        canonical = self.transformer.transform(semantic)
        validation = self.validator.validate(canonical)
        assessments = self.terminology.assess_message(canonical)
        terminology_counts = Counter(item.validation.status.value for item in assessments)

        if not validation.is_valid:
            return ProcessingOutcome(
                status=ProcessingStatus.REJECTED,
                source_message_id=canonical.source_message_id,
                source_event_code=canonical.source_event_code,
                validation_error_count=len(validation.errors),
                validation_warning_count=len(validation.warnings),
                terminology_status_counts=tuple(sorted(terminology_counts.items())),
            )

        if canonical.patient is None:
            return ProcessingOutcome(
                status=ProcessingStatus.PROCESSED,
                source_message_id=canonical.source_message_id,
                source_event_code=canonical.source_event_code,
                validation_error_count=len(validation.errors),
                validation_warning_count=len(validation.warnings),
                terminology_status_counts=tuple(sorted(terminology_counts.items())),
            )

        normalized_source_system = source_system.strip()
        if not normalized_source_system:
            raise ValueError("source_system must not be blank")
        source_record_id = self._source_record_id(
            canonical.patient.primary_identifier.system,
            canonical.patient.primary_identifier.type_code,
            canonical.patient.primary_identifier.value,
            canonical.source_message_id,
            normalized_source_system,
            scope,
        )
        record = IdentityRecord(
            record_id=source_record_id,
            source_system=normalized_source_system,
            scope=scope,
            patient=canonical.patient,
        )
        resolution = self.identity.resolve(record)
        self.identity.index(record)
        master_service = MasterPatientIdentityService(self.master_repository)
        master_patient_id: UUID | None = None
        review_case_id: UUID | None = None

        if resolution.status is IdentityResolutionStatus.NO_MATCH:
            master = master_service.create_master_and_link(record, actor_id=actor_id)
            master_patient_id = master.master_patient_id
        elif resolution.status is IdentityResolutionStatus.DETERMINISTIC_MATCH:
            if resolution.selected_record_id is None:
                raise RuntimeError("deterministic identity result is missing selected record")
            candidate = self.identity.store.get(resolution.selected_record_id)
            if candidate is None:
                raise RuntimeError("selected identity candidate no longer exists")
            candidate_link = self.master_repository.active_link_for_record(
                scope=candidate.scope,
                source_record_id=candidate.record_id,
                source_system=candidate.source_system,
            )
            if candidate_link is None:
                master = master_service.create_master_and_link(
                    candidate,
                    actor_id=actor_id,
                    reason=IdentityDecisionReason.DETERMINISTIC_IDENTIFIER,
                )
                master_patient_id = master.master_patient_id
            else:
                master_patient_id = candidate_link.master_patient_id
            master_service.link_to_master(
                master_patient_id,
                record,
                actor_id=actor_id,
                reason=IdentityDecisionReason.DETERMINISTIC_IDENTIFIER,
            )
        elif resolution.requires_manual_review:
            case = master_service.open_review(record, resolution, actor_id=actor_id)
            review_case_id = case.review_case_id

        clinical_message_id: UUID | None = None
        clinical_write_status: ClinicalWriteStatus | None = None
        if master_patient_id is not None and self.clinical_writer is not None:
            write = self.clinical_writer.persist(
                message=canonical,
                master_patient_id=master_patient_id,
                scope=scope,
                source_system=normalized_source_system,
                received_at=received_at,
            )
            clinical_message_id = write.clinical_message_id
            clinical_write_status = write.status

        return ProcessingOutcome(
            status=ProcessingStatus.PROCESSED,
            source_message_id=canonical.source_message_id,
            source_event_code=canonical.source_event_code,
            validation_error_count=len(validation.errors),
            validation_warning_count=len(validation.warnings),
            terminology_status_counts=tuple(sorted(terminology_counts.items())),
            identity_status=resolution.status,
            source_record_id=source_record_id,
            master_patient_id=master_patient_id,
            review_case_id=review_case_id,
            clinical_message_id=clinical_message_id,
            clinical_write_status=clinical_write_status,
        )

    def _source_record_id(
        self,
        identifier_system: str | None,
        identifier_type: str | None,
        identifier_value: str,
        source_message_id: str,
        source_system: str,
        scope: IdentityScope,
    ) -> str:
        namespace = (
            f"source-record\x1f{scope.tenant_id}\x1f{scope.identity_domain}\x1f"
            f"{source_system}\x1f{identifier_system or ''}\x1f{identifier_type or ''}"
        )
        value = identifier_value.strip() or source_message_id
        return self.record_id_encoder.encode(namespace, value)
