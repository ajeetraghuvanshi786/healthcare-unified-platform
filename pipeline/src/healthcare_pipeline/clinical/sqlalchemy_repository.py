from __future__ import annotations

import base64
import binascii
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from healthcare_pipeline.canonical import CanonicalClinicalMessage, Coding
from healthcare_pipeline.clinical.exceptions import ClinicalMessageConflict
from healthcare_pipeline.clinical.models import (
    ClinicalListItem,
    ClinicalProvenance,
    ClinicalWriteResult,
    ClinicalWriteStatus,
    PatientClinicalSummary,
    TimelineEvent,
    TimelinePage,
)
from healthcare_pipeline.clinical.repository import ClinicalRepository
from healthcare_pipeline.clinical.serialization import canonical_sha256, to_json_value
from healthcare_pipeline.identity.models import IdentityScope
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

ClinicalResourceRecord = (
    ClinicalEncounterRecord
    | ClinicalDiagnosisRecord
    | ClinicalObservationRecord
    | ClinicalAllergyRecord
    | ClinicalMedicationOrderRecord
    | ClinicalMedicationAdministrationRecord
    | ClinicalCoverageRecord
)


def _coding_parts(coding: Coding | None) -> tuple[str | None, str | None, str | None]:
    if coding is None:
        return None, None, None
    return coding.system, coding.code, coding.display


def _display(coding: Coding | None, fallback: str) -> str:
    if coding is None:
        return fallback
    return coding.display or coding.code or fallback


def _snapshot_without(value: object, *excluded_fields: str) -> dict[str, object]:
    snapshot = cast(dict[str, object], to_json_value(value))
    for field_name in excluded_fields:
        snapshot.pop(field_name, None)
    return snapshot


def _aware(timestamp: datetime) -> datetime:
    return timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=UTC)


def _timeline_cursor(timestamp: datetime, event_id: UUID) -> str:
    raw = f"{_aware(timestamp).isoformat()}|{event_id}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")




def _timeline_details(row: ClinicalResourceRecord) -> dict[str, object]:
    if isinstance(row, ClinicalEncounterRecord):
        return {
            "encounter_class": row.encounter_class,
            "service_type": row.service_type,
            "start_at": row.start_at.isoformat() if row.start_at else None,
            "end_at": row.end_at.isoformat() if row.end_at else None,
        }
    if isinstance(row, ClinicalDiagnosisRecord):
        return {
            "code_system": row.code_system,
            "code": row.code,
            "display": row.display,
            "diagnosis_type": row.diagnosis_type,
        }
    if isinstance(row, ClinicalObservationRecord):
        return {
            "code_system": row.code_system,
            "code": row.code,
            "display": row.display,
            "values": row.values_json,
            "unit": row.unit_display or row.unit_code,
            "abnormal_flags": row.abnormal_flags,
        }
    if isinstance(row, ClinicalAllergyRecord):
        return {
            "allergen_code": row.allergen_code,
            "allergen_display": row.allergen_display,
            "severity": row.severity_display,
            "reactions": row.reactions,
        }
    if isinstance(row, ClinicalMedicationOrderRecord):
        return {
            "medication_code": row.medication_code,
            "medication_display": row.medication_display,
            "status": row.status,
        }
    if isinstance(row, ClinicalMedicationAdministrationRecord):
        return {
            "medication_code": row.medication_code,
            "medication_display": row.medication_display,
            "status": row.status,
        }
    if isinstance(row, ClinicalCoverageRecord):
        return {
            "payer_name": row.payer_name,
            "effective_date": (
                row.effective_date.isoformat() if row.effective_date else None
            ),
            "expiration_date": (
                row.expiration_date.isoformat() if row.expiration_date else None
            ),
        }
    raise TypeError("unsupported clinical timeline resource")


def _decode_cursor(value: str) -> tuple[datetime, UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        timestamp, event_id = decoded.rsplit("|", 1)
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            raise ValueError("timeline cursor timestamp must be timezone-aware")
        return parsed, UUID(event_id)
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid timeline cursor") from exc


class SQLAlchemyClinicalRepository(ClinicalRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def persist_message(
        self,
        *,
        message: CanonicalClinicalMessage,
        master_patient_id: UUID,
        scope: IdentityScope,
        source_system: str,
        received_at: datetime,
    ) -> ClinicalWriteResult:
        normalized_source = source_system.strip()
        if not normalized_source:
            raise ValueError("source_system must not be blank")
        if received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")

        digest = canonical_sha256(message)
        existing = self.session.scalar(
            select(ClinicalMessageRecord).where(
                ClinicalMessageRecord.tenant_id == scope.tenant_id,
                ClinicalMessageRecord.identity_domain == scope.identity_domain,
                ClinicalMessageRecord.source_system == normalized_source,
                ClinicalMessageRecord.source_message_id == message.source_message_id,
            )
        )
        if existing is not None:
            if existing.canonical_hash != digest or existing.master_patient_id != master_patient_id:
                raise ClinicalMessageConflict(
                    "source message identity already exists with different canonical content"
                )
            return ClinicalWriteResult(
                ClinicalWriteStatus.ALREADY_PROCESSED,
                existing.id,
            )

        now = datetime.now(UTC)
        message_row = ClinicalMessageRecord(
            tenant_id=scope.tenant_id,
            identity_domain=scope.identity_domain,
            master_patient_id=master_patient_id,
            source_system=normalized_source,
            source_message_id=message.source_message_id,
            source_event_code=message.source_event_code,
            source_format=message.source_format,
            canonical_hash=digest,
            received_at=received_at,
            created_at=now,
        )
        try:
            with self.session.begin_nested():
                self.session.add(message_row)
                self.session.flush()
        except IntegrityError as exc:
            concurrent = self.session.scalar(
                select(ClinicalMessageRecord).where(
                    ClinicalMessageRecord.tenant_id == scope.tenant_id,
                    ClinicalMessageRecord.identity_domain == scope.identity_domain,
                    ClinicalMessageRecord.source_system == normalized_source,
                    ClinicalMessageRecord.source_message_id == message.source_message_id,
                )
            )
            if concurrent is None:
                raise
            if (
                concurrent.canonical_hash != digest
                or concurrent.master_patient_id != master_patient_id
            ):
                raise ClinicalMessageConflict(
                    "source message identity already exists with different canonical content"
                ) from exc
            return ClinicalWriteResult(
                ClinicalWriteStatus.ALREADY_PROCESSED,
                concurrent.id,
            )

        if message.encounter is not None:
            encounter = message.encounter
            encounter_row = ClinicalEncounterRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                encounter_class=encounter.encounter_class.value,
                start_at=encounter.period.start if encounter.period else None,
                end_at=encounter.period.end if encounter.period else None,
                service_type=encounter.service_type,
                admission_type=encounter.admission_type,
                discharge_disposition=encounter.discharge_disposition,
                snapshot=_snapshot_without(encounter, "identifiers"),
            )
            self._add_resource(
                message_row,
                encounter_row,
                "encounter",
                encounter_row.start_at or received_at,
                encounter.encounter_class.value,
                scope,
            )

        for diagnosis in message.diagnoses:
            system, code, display = _coding_parts(diagnosis.code)
            diagnosis_row = ClinicalDiagnosisRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                code_system=system,
                code=code,
                display=display,
                diagnosis_type=diagnosis.diagnosis_type,
                priority=diagnosis.priority,
                recorded_at=diagnosis.recorded_datetime,
                snapshot=to_json_value(diagnosis),
            )
            self._add_resource(
                message_row,
                diagnosis_row,
                "diagnosis",
                diagnosis_row.recorded_at or received_at,
                _display(diagnosis.code, "Diagnosis"),
                scope,
            )

        for order in message.observation_orders:
            order_system, order_code, order_display = _coding_parts(order.service)
            for observation in order.results:
                system, code, display = _coding_parts(observation.code)
                unit_system, unit_code, unit_display = _coding_parts(observation.units)
                observation_row = ClinicalObservationRecord(
                    clinical_message_id=message_row.id,
                    tenant_id=scope.tenant_id,
                    identity_domain=scope.identity_domain,
                    master_patient_id=master_patient_id,
                    order_service_system=order_system,
                    order_service_code=order_code,
                    order_service_display=order_display,
                    code_system=system,
                    code=code,
                    display=display,
                    status=observation.status,
                    value_type=observation.value_type,
                    values_json=list(observation.values),
                    unit_system=unit_system,
                    unit_code=unit_code,
                    unit_display=unit_display,
                    reference_range=observation.reference_range,
                    abnormal_flags=list(observation.abnormal_flags),
                    effective_at=observation.effective_datetime or order.observation_datetime,
                    snapshot=to_json_value(observation),
                )
                self._add_resource(
                    message_row,
                    observation_row,
                    "observation",
                    observation_row.effective_at or received_at,
                    _display(observation.code, "Observation"),
                    scope,
                )

        for allergy in message.allergies:
            system, code, display = _coding_parts(allergy.allergen)
            allergy_row = ClinicalAllergyRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                allergen_system=system,
                allergen_code=code,
                allergen_display=display,
                severity_display=_display(allergy.severity, "") or None,
                reactions=list(allergy.reactions),
                identified_date=allergy.identified_date,
                snapshot=to_json_value(allergy),
            )
            occurred = (
                datetime.combine(allergy.identified_date, datetime.min.time(), tzinfo=UTC)
                if allergy.identified_date
                else received_at
            )
            self._add_resource(
                message_row,
                allergy_row,
                "allergy",
                occurred,
                _display(allergy.allergen, "Allergy"),
                scope,
            )

        for medication in message.medication_orders:
            system, code, display = _coding_parts(medication.medication)
            medication_order_row = ClinicalMedicationOrderRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                medication_system=system,
                medication_code=code,
                medication_display=display,
                status=medication.status,
                snapshot=_snapshot_without(medication, "identifiers"),
            )
            self._add_resource(
                message_row,
                medication_order_row,
                "medication_order",
                received_at,
                _display(medication.medication, "Medication order"),
                scope,
            )

        for administration in message.medication_administrations:
            system, code, display = _coding_parts(administration.medication)
            administration_row = ClinicalMedicationAdministrationRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                medication_system=system,
                medication_code=code,
                medication_display=display,
                status=administration.status,
                start_at=administration.start_datetime,
                end_at=administration.end_datetime,
                snapshot=to_json_value(administration),
            )
            self._add_resource(
                message_row,
                administration_row,
                "medication_administration",
                administration.start_datetime,
                _display(administration.medication, "Medication administration"),
                scope,
            )

        for coverage in message.coverages:
            coverage_row = ClinicalCoverageRecord(
                clinical_message_id=message_row.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=master_patient_id,
                payer_name=coverage.payer_name,
                group_number=coverage.group_number,
                effective_date=coverage.effective_date,
                expiration_date=coverage.expiration_date,
                snapshot=_snapshot_without(
                    coverage,
                    "policy_identifiers",
                    "payer_identifiers",
                    "payer_addresses",
                    "payer_telecom",
                    "subscriber_names",
                    "subscriber_identifiers",
                ),
            )
            occurred = (
                datetime.combine(coverage.effective_date, datetime.min.time(), tzinfo=UTC)
                if coverage.effective_date
                else received_at
            )
            self._add_resource(
                message_row,
                coverage_row,
                "coverage",
                occurred,
                coverage.payer_name or "Coverage",
                scope,
            )

        return ClinicalWriteResult(ClinicalWriteStatus.CREATED, message_row.id)

    def _add_resource(
        self,
        message: ClinicalMessageRecord,
        row: ClinicalResourceRecord,
        resource_type: str,
        occurred_at: datetime,
        display: str,
        scope: IdentityScope,
    ) -> None:
        self.session.add(row)
        self.session.flush()
        resource_id = row.id
        timeline_details = _timeline_details(row)
        self.session.add(
            ClinicalProvenanceRecord(
                clinical_message_id=message.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=message.master_patient_id,
                resource_type=resource_type,
                resource_id=resource_id,
                source_system=message.source_system,
                source_message_id=message.source_message_id,
                source_event_code=message.source_event_code,
                recorded_at=message.received_at,
            )
        )
        self.session.add(
            ClinicalTimelineEventRecord(
                clinical_message_id=message.id,
                tenant_id=scope.tenant_id,
                identity_domain=scope.identity_domain,
                master_patient_id=message.master_patient_id,
                event_type=resource_type,
                resource_id=resource_id,
                occurred_at=occurred_at,
                display=display[:512],
                details=timeline_details,
            )
        )

    def summary(
        self,
        *,
        master_patient_id: UUID,
        scope: IdentityScope,
    ) -> PatientClinicalSummary:
        def scoped_count(model: Any) -> int:
            value = self.session.scalar(
                select(func.count()).select_from(model).where(
                    model.tenant_id == scope.tenant_id,
                    model.identity_domain == scope.identity_domain,
                    model.master_patient_id == master_patient_id,
                )
            )
            return int(value or 0)

        latest = self.session.scalar(
            select(func.max(ClinicalTimelineEventRecord.occurred_at)).where(
                ClinicalTimelineEventRecord.tenant_id == scope.tenant_id,
                ClinicalTimelineEventRecord.identity_domain == scope.identity_domain,
                ClinicalTimelineEventRecord.master_patient_id == master_patient_id,
            )
        )
        if latest is not None:
            latest = _aware(latest)
        return PatientClinicalSummary(
            master_patient_id=master_patient_id,
            encounter_count=scoped_count(ClinicalEncounterRecord),
            diagnosis_count=scoped_count(ClinicalDiagnosisRecord),
            observation_count=scoped_count(ClinicalObservationRecord),
            allergy_count=scoped_count(ClinicalAllergyRecord),
            medication_order_count=scoped_count(ClinicalMedicationOrderRecord),
            medication_administration_count=scoped_count(
                ClinicalMedicationAdministrationRecord
            ),
            coverage_count=scoped_count(ClinicalCoverageRecord),
            latest_event_at=latest,
        )

    def timeline(
        self,
        *,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int,
        cursor: str | None,
    ) -> TimelinePage:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        query = select(ClinicalTimelineEventRecord).where(
            ClinicalTimelineEventRecord.tenant_id == scope.tenant_id,
            ClinicalTimelineEventRecord.identity_domain == scope.identity_domain,
            ClinicalTimelineEventRecord.master_patient_id == master_patient_id,
        )
        if cursor is not None:
            timestamp, event_id = _decode_cursor(cursor)
            query = query.where(
                or_(
                    ClinicalTimelineEventRecord.occurred_at < timestamp,
                    and_(
                        ClinicalTimelineEventRecord.occurred_at == timestamp,
                        ClinicalTimelineEventRecord.id < event_id,
                    ),
                )
            )
        rows = self.session.scalars(
            query.order_by(
                ClinicalTimelineEventRecord.occurred_at.desc(),
                ClinicalTimelineEventRecord.id.desc(),
            ).limit(limit + 1)
        ).all()
        has_more = len(rows) > limit
        visible = rows[:limit]
        items = tuple(
            TimelineEvent(
                event_id=row.id,
                event_type=row.event_type,
                resource_id=row.resource_id,
                occurred_at=_aware(row.occurred_at),
                display=row.display,
                details=row.details,
            )
            for row in visible
        )
        next_cursor = None
        if has_more and visible:
            last = visible[-1]
            next_cursor = _timeline_cursor(last.occurred_at, last.id)
        return TimelinePage(items=items, next_cursor=next_cursor)

    def list_resources(
        self,
        *,
        resource_type: str,
        master_patient_id: UUID,
        scope: IdentityScope,
        limit: int,
    ) -> tuple[ClinicalListItem, ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        rows: Sequence[Any]
        if resource_type == "encounter":
            rows = self.session.scalars(
                select(ClinicalEncounterRecord)
                .where(
                    ClinicalEncounterRecord.tenant_id == scope.tenant_id,
                    ClinicalEncounterRecord.identity_domain == scope.identity_domain,
                    ClinicalEncounterRecord.master_patient_id == master_patient_id,
                )
                .order_by(
                    ClinicalEncounterRecord.start_at.desc(),
                    ClinicalEncounterRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        elif resource_type == "diagnosis":
            rows = self.session.scalars(
                select(ClinicalDiagnosisRecord)
                .where(
                    ClinicalDiagnosisRecord.tenant_id == scope.tenant_id,
                    ClinicalDiagnosisRecord.identity_domain == scope.identity_domain,
                    ClinicalDiagnosisRecord.master_patient_id == master_patient_id,
                )
                .order_by(
                    ClinicalDiagnosisRecord.recorded_at.desc(),
                    ClinicalDiagnosisRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        elif resource_type == "observation":
            rows = self.session.scalars(
                select(ClinicalObservationRecord)
                .where(
                    ClinicalObservationRecord.tenant_id == scope.tenant_id,
                    ClinicalObservationRecord.identity_domain == scope.identity_domain,
                    ClinicalObservationRecord.master_patient_id == master_patient_id,
                )
                .order_by(
                    ClinicalObservationRecord.effective_at.desc(),
                    ClinicalObservationRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        elif resource_type == "allergy":
            rows = self.session.scalars(
                select(ClinicalAllergyRecord)
                .where(
                    ClinicalAllergyRecord.tenant_id == scope.tenant_id,
                    ClinicalAllergyRecord.identity_domain == scope.identity_domain,
                    ClinicalAllergyRecord.master_patient_id == master_patient_id,
                )
                .order_by(
                    ClinicalAllergyRecord.identified_date.desc(),
                    ClinicalAllergyRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        elif resource_type == "medication_order":
            rows = self.session.scalars(
                select(ClinicalMedicationOrderRecord)
                .where(
                    ClinicalMedicationOrderRecord.tenant_id == scope.tenant_id,
                    ClinicalMedicationOrderRecord.identity_domain == scope.identity_domain,
                    ClinicalMedicationOrderRecord.master_patient_id == master_patient_id,
                )
                .order_by(ClinicalMedicationOrderRecord.id.desc())
                .limit(limit)
            ).all()
        elif resource_type == "medication_administration":
            rows = self.session.scalars(
                select(ClinicalMedicationAdministrationRecord)
                .where(
                    ClinicalMedicationAdministrationRecord.tenant_id == scope.tenant_id,
                    ClinicalMedicationAdministrationRecord.identity_domain
                    == scope.identity_domain,
                    ClinicalMedicationAdministrationRecord.master_patient_id
                    == master_patient_id,
                )
                .order_by(
                    ClinicalMedicationAdministrationRecord.start_at.desc(),
                    ClinicalMedicationAdministrationRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        elif resource_type == "coverage":
            rows = self.session.scalars(
                select(ClinicalCoverageRecord)
                .where(
                    ClinicalCoverageRecord.tenant_id == scope.tenant_id,
                    ClinicalCoverageRecord.identity_domain == scope.identity_domain,
                    ClinicalCoverageRecord.master_patient_id == master_patient_id,
                )
                .order_by(
                    ClinicalCoverageRecord.effective_date.desc(),
                    ClinicalCoverageRecord.id.desc(),
                )
                .limit(limit)
            ).all()
        else:
            raise ValueError("unsupported clinical resource type")
        return tuple(self._list_item(resource_type, row) for row in rows)

    def provenance(
        self,
        *,
        resource_type: str,
        resource_id: UUID,
        master_patient_id: UUID,
        scope: IdentityScope,
    ) -> ClinicalProvenance | None:
        row = self.session.scalar(
            select(ClinicalProvenanceRecord).where(
                ClinicalProvenanceRecord.tenant_id == scope.tenant_id,
                ClinicalProvenanceRecord.identity_domain == scope.identity_domain,
                ClinicalProvenanceRecord.master_patient_id == master_patient_id,
                ClinicalProvenanceRecord.resource_type == resource_type,
                ClinicalProvenanceRecord.resource_id == resource_id,
            )
        )
        if row is None:
            return None
        return ClinicalProvenance(
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            source_system=row.source_system,
            source_message_id=row.source_message_id,
            source_event_code=row.source_event_code,
            recorded_at=_aware(row.recorded_at),
        )

    @staticmethod
    def _list_item(resource_type: str, row: Any) -> ClinicalListItem:
        snapshot = cast(dict[str, object], row.snapshot)
        occurred_at: datetime | date | None = None
        display = resource_type.replace("_", " ").title()
        for attribute in (
            "effective_at",
            "recorded_at",
            "start_at",
            "identified_date",
            "effective_date",
        ):
            value = getattr(row, attribute, None)
            if value is not None:
                occurred_at = value
                break
        for attribute in (
            "display",
            "allergen_display",
            "medication_display",
            "payer_name",
            "encounter_class",
        ):
            value = getattr(row, attribute, None)
            if value:
                display = str(value)
                break
        return ClinicalListItem(
            resource_id=cast(UUID, row.id),
            resource_type=resource_type,
            occurred_at=occurred_at,
            display=display,
            details=snapshot,
        )
