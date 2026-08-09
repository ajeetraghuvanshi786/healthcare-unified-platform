from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.clinical.allergy import Allergy
from healthcare_pipeline.canonical.clinical.diagnosis import Diagnosis
from healthcare_pipeline.canonical.clinical.observation_order import ObservationOrder
from healthcare_pipeline.canonical.common._validation import normalize_required
from healthcare_pipeline.canonical.demographics.patient import Patient
from healthcare_pipeline.canonical.encounters.encounter import Encounter
from healthcare_pipeline.canonical.financial.coverage import Coverage
from healthcare_pipeline.canonical.medication.administration import MedicationAdministration
from healthcare_pipeline.canonical.medication.order import MedicationOrder


@dataclass(frozen=True, slots=True)
class CanonicalClinicalMessage:
    """Format-independent semantic aggregate passed to downstream platform services."""

    source_format: str
    source_message_id: str
    source_event_code: str
    patient: Patient | None = None
    encounter: Encounter | None = None
    coverages: tuple[Coverage, ...] = ()
    diagnoses: tuple[Diagnosis, ...] = ()
    allergies: tuple[Allergy, ...] = ()
    observation_orders: tuple[ObservationOrder, ...] = ()
    medication_orders: tuple[MedicationOrder, ...] = ()
    medication_administrations: tuple[MedicationAdministration, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("source_format", "source_message_id", "source_event_code"):
            object.__setattr__(
                self,
                field_name,
                normalize_required(getattr(self, field_name), field_name),
            )
        if self.patient is not None and not isinstance(self.patient, Patient):
            raise TypeError("patient must be a Patient or None")
        if self.encounter is not None and not isinstance(self.encounter, Encounter):
            raise TypeError("encounter must be an Encounter or None")
        for field_name, expected_type in (
            ("coverages", Coverage),
            ("diagnoses", Diagnosis),
            ("allergies", Allergy),
            ("observation_orders", ObservationOrder),
            ("medication_orders", MedicationOrder),
            ("medication_administrations", MedicationAdministration),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
