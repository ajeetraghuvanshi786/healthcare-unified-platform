from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.canonical.common._validation import normalize_optional
from healthcare_pipeline.canonical.common.address import Address
from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.canonical.common.contact_point import ContactPoint
from healthcare_pipeline.canonical.common.human_name import HumanName
from healthcare_pipeline.canonical.common.identifier import Identifier


@dataclass(frozen=True, slots=True)
class Coverage:
    """Canonical insurance or payer coverage independent of IN1/FHIR representations."""

    policy_identifiers: tuple[Identifier, ...] = ()
    plan: Coding | None = None
    payer_identifiers: tuple[Identifier, ...] = ()
    payer_name: str | None = None
    payer_addresses: tuple[Address, ...] = ()
    payer_telecom: tuple[ContactPoint, ...] = ()
    group_number: str | None = None
    group_name: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    subscriber_names: tuple[HumanName, ...] = ()
    subscriber_identifiers: tuple[Identifier, ...] = ()
    relationship: Coding | None = None

    def __post_init__(self) -> None:
        for field_name, expected_type in (
            ("policy_identifiers", Identifier),
            ("payer_identifiers", Identifier),
            ("payer_addresses", Address),
            ("payer_telecom", ContactPoint),
            ("subscriber_names", HumanName),
            ("subscriber_identifiers", Identifier),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        for field_name in ("payer_name", "group_number", "group_name"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if (
            self.effective_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.effective_date
        ):
            raise ValueError("expiration_date must not precede effective_date")
