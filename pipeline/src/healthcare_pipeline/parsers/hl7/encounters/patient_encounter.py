from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.encounters.patient_class import PatientClass
from healthcare_pipeline.parsers.hl7.encounters.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class PatientEncounter:
    """Immutable semantic encounter representation produced from PV1."""

    patient_class: PatientClass
    set_id: int | None = None
    assigned_location: PatientLocation | None = None
    prior_location: PatientLocation | None = None
    temporary_location: PatientLocation | None = None
    attending_provider: Provider | None = None
    referring_provider: Provider | None = None
    consulting_providers: tuple[Provider, ...] = ()
    admitting_provider: Provider | None = None
    visit_number: PatientIdentifier | None = None
    hospital_service: str | None = None
    admission_type: str | None = None
    patient_type: str | None = None
    financial_class: str | None = None
    discharge_disposition: str | None = None
    servicing_facility: str | None = None
    admit_datetime: datetime | None = None
    discharge_datetime: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.patient_class, PatientClass):
            raise TypeError("patient_class must be a PatientClass")
        if self.set_id is not None and self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        object.__setattr__(self, "consulting_providers", tuple(self.consulting_providers))
        if not all(isinstance(value, Provider) for value in self.consulting_providers):
            raise TypeError("consulting_providers must contain Provider values")
        keys = [provider.identity_key for provider in self.consulting_providers]
        if len(keys) != len(set(keys)):
            raise ValueError("consulting_providers must not contain duplicates")
        for field_name in (
            "hospital_service",
            "admission_type",
            "patient_type",
            "financial_class",
            "discharge_disposition",
            "servicing_facility",
        ):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        for field_name in ("admit_datetime", "discharge_datetime"):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if (
            self.admit_datetime is not None
            and self.discharge_datetime is not None
            and self.discharge_datetime < self.admit_datetime
        ):
            raise ValueError("discharge_datetime must not precede admit_datetime")

    @property
    def is_active(self) -> bool:
        return self.discharge_datetime is None
