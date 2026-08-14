from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol
from uuid import UUID

from healthcare_pipeline.identity.master.models import (
    IdentityDecisionEvent,
    MasterPatient,
    MasterPatientLink,
    MasterPatientLinkStatus,
    ReviewCase,
)
from healthcare_pipeline.identity.models import IdentityScope


class MasterIdentityRepository(Protocol):
    """Persistence port for master identity state and append-only decision audit."""

    def create_master(self, master: MasterPatient) -> None: ...

    def get_master(self, master_patient_id: UUID) -> MasterPatient | None: ...

    def active_link_for_record(
        self,
        *,
        scope: IdentityScope,
        source_record_id: str,
        source_system: str | None = None,
    ) -> MasterPatientLink | None: ...

    def active_links_for_master(self, master_patient_id: UUID) -> tuple[MasterPatientLink, ...]: ...

    def save_link(self, link: MasterPatientLink) -> None: ...

    def save_review_case(self, review_case: ReviewCase) -> None: ...

    def get_review_case(self, review_case_id: UUID) -> ReviewCase | None: ...

    def append_event(self, event: IdentityDecisionEvent) -> None: ...

    def events(self) -> tuple[IdentityDecisionEvent, ...]: ...


@dataclass(slots=True)
class InMemoryMasterIdentityRepository:
    """Thread-safe development/test repository implementing production repository semantics."""

    _masters: dict[UUID, MasterPatient] = field(default_factory=dict, init=False, repr=False)
    _links_by_record: dict[tuple[IdentityScope, str, str], MasterPatientLink] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _links_by_master: dict[UUID, dict[tuple[str, str], MasterPatientLink]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _reviews: dict[UUID, ReviewCase] = field(default_factory=dict, init=False, repr=False)
    _events: list[IdentityDecisionEvent] = field(default_factory=list, init=False, repr=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    def create_master(self, master: MasterPatient) -> None:
        with self._lock:
            existing = self._masters.get(master.master_patient_id)
            if existing is not None and existing != master:
                raise ValueError("master_patient_id already exists")
            self._masters[master.master_patient_id] = master

    def get_master(self, master_patient_id: UUID) -> MasterPatient | None:
        with self._lock:
            return self._masters.get(master_patient_id)

    def active_link_for_record(
        self,
        *,
        scope: IdentityScope,
        source_record_id: str,
        source_system: str | None = None,
    ) -> MasterPatientLink | None:
        normalized_id = source_record_id.strip()
        with self._lock:
            if source_system is not None:
                link = self._links_by_record.get((scope, source_system.strip(), normalized_id))
                if link is None or link.status is not MasterPatientLinkStatus.ACTIVE:
                    return None
                return link
            matches = [
                link
                for (candidate_scope, _system, candidate_id), link in self._links_by_record.items()
                if candidate_scope == scope
                and candidate_id == normalized_id
                and link.status is MasterPatientLinkStatus.ACTIVE
            ]
            if len(matches) > 1:
                raise ValueError("source_record_id is ambiguous across source systems")
            return matches[0] if matches else None

    def active_links_for_master(self, master_patient_id: UUID) -> tuple[MasterPatientLink, ...]:
        with self._lock:
            links = self._links_by_master.get(master_patient_id, {})
            return tuple(
                sorted(
                    (
                        link
                        for link in links.values()
                        if link.status is MasterPatientLinkStatus.ACTIVE
                    ),
                    key=lambda item: (item.source_system, item.source_record_id),
                )
            )

    def save_link(self, link: MasterPatientLink) -> None:
        with self._lock:
            master = self._masters.get(link.master_patient_id)
            if master is None:
                raise ValueError("master patient does not exist")
            if master.scope != link.scope:
                raise ValueError("link scope does not match master patient scope")

            key = (link.scope, link.source_system, link.source_record_id)
            current = self._links_by_record.get(key)
            if (
                link.status is MasterPatientLinkStatus.ACTIVE
                and current is not None
                and current.status is MasterPatientLinkStatus.ACTIVE
                and current.master_patient_id != link.master_patient_id
            ):
                raise ValueError("source record is already linked to another master patient")

            self._links_by_record[key] = link
            by_master = self._links_by_master.setdefault(link.master_patient_id, {})
            by_master[(link.source_system, link.source_record_id)] = link

    def save_review_case(self, review_case: ReviewCase) -> None:
        with self._lock:
            existing = self._reviews.get(review_case.review_case_id)
            if existing is not None and existing.scope != review_case.scope:
                raise ValueError("review_case_id scope cannot change")
            self._reviews[review_case.review_case_id] = review_case

    def get_review_case(self, review_case_id: UUID) -> ReviewCase | None:
        with self._lock:
            return self._reviews.get(review_case_id)

    def append_event(self, event: IdentityDecisionEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events(self) -> tuple[IdentityDecisionEvent, ...]:
        with self._lock:
            return tuple(self._events)
