from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class PharmacyEncodedOrder:
    """Immutable semantic pharmacy/treatment encoded order from RXE."""

    give_code: CodedValue
    quantity_timing: str | None = None
    give_amount_minimum: Decimal | None = None
    give_amount_maximum: Decimal | None = None
    give_units: CodedValue | None = None
    give_dosage_form: CodedValue | None = None
    provider_instructions: tuple[CodedValue, ...] = ()
    dispense_amount: Decimal | None = None
    dispense_units: CodedValue | None = None
    number_of_refills: int | None = None
    ordering_providers: tuple[Provider, ...] = ()
    provider_dea_number: str | None = None
    pharmacist_verification_identifier: str | None = None
    pharmacy_treatment_supplier_instructions: tuple[CodedValue, ...] = ()
    give_rate_amount: Decimal | None = None
    give_rate_units: CodedValue | None = None
    give_strength: Decimal | None = None
    give_strength_units: CodedValue | None = None
    supplemental_codes: tuple[CodedValue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.give_code, CodedValue):
            raise TypeError("give_code must be a CodedValue")
        object.__setattr__(
            self,
            "quantity_timing",
            normalize_optional(self.quantity_timing, "quantity_timing"),
        )
        for field_name in ("provider_dea_number", "pharmacist_verification_identifier"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        for field_name in (
            "give_amount_minimum",
            "give_amount_maximum",
            "dispense_amount",
            "give_rate_amount",
            "give_strength",
        ):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must not be negative")
        if (
            self.give_amount_minimum is not None
            and self.give_amount_maximum is not None
            and self.give_amount_maximum < self.give_amount_minimum
        ):
            raise ValueError("give_amount_maximum must not be less than give_amount_minimum")
        if self.number_of_refills is not None and self.number_of_refills < 0:
            raise ValueError("number_of_refills must not be negative")
        for field_name, expected_type in (
            ("provider_instructions", CodedValue),
            ("ordering_providers", Provider),
            ("pharmacy_treatment_supplier_instructions", CodedValue),
            ("supplemental_codes", CodedValue),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
