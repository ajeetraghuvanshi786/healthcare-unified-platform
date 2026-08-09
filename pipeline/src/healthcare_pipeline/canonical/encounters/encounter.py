from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import normalize_optional
from healthcare_pipeline.canonical.common.identifier import Identifier
from healthcare_pipeline.canonical.common.location import Location
from healthcare_pipeline.canonical.common.period import Period


class EncounterClass(StrEnum):
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    PREADMIT = "preadmit"
    RECURRING = "recurring"
    OBSTETRICS = "obstetrics"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Encounter:
    """Canonical healthcare interaction such as a visit, admission, or ED stay."""

    encounter_class: EncounterClass
    identifiers: tuple[Identifier, ...] = ()
    period: Period | None = None
    locations: tuple[Location, ...] = ()
    attending_providers: tuple[Provider, ...] = ()
    referring_providers: tuple[Provider, ...] = ()
    consulting_providers: tuple[Provider, ...] = ()
    admitting_providers: tuple[Provider, ...] = ()
    service_type: str | None = None
    admission_type: str | None = None
    discharge_disposition: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.encounter_class, EncounterClass):
            raise TypeError("encounter_class must be an EncounterClass")
        for field_name, expected_type in (
            ("identifiers", Identifier),
            ("locations", Location),
            ("attending_providers", Provider),
            ("referring_providers", Provider),
            ("consulting_providers", Provider),
            ("admitting_providers", Provider),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        if self.period is not None and not isinstance(self.period, Period):
            raise TypeError("period must be a Period or None")
        for field_name in ("service_type", "admission_type", "discharge_disposition"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
