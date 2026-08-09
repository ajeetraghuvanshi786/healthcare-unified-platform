from __future__ import annotations

from collections.abc import Iterator

from healthcare_pipeline.canonical.clinical.allergy import Allergy
from healthcare_pipeline.canonical.clinical.diagnosis import Diagnosis
from healthcare_pipeline.canonical.clinical.observation import Observation
from healthcare_pipeline.canonical.clinical.observation_order import ObservationOrder
from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.canonical.common.identifier import Identifier
from healthcare_pipeline.canonical.financial.coverage import Coverage
from healthcare_pipeline.canonical.medication.administration import MedicationAdministration
from healthcare_pipeline.canonical.medication.order import MedicationOrder
from healthcare_pipeline.canonical.medication.route import MedicationRoute
from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage


def iter_identifiers(message: CanonicalClinicalMessage) -> Iterator[tuple[str, Identifier]]:
    """Yield identifiers with PHI-safe structural paths for cross-cutting services."""

    if message.patient is not None:
        for index, identifier in enumerate(message.patient.identifiers):
            yield f"patient.identifiers[{index}]", identifier
        for index, identifier in enumerate(message.patient.account_identifiers):
            yield f"patient.account_identifiers[{index}]", identifier
    if message.encounter is not None:
        for index, identifier in enumerate(message.encounter.identifiers):
            yield f"encounter.identifiers[{index}]", identifier
    for coverage_index, coverage in enumerate(message.coverages):
        yield from _coverage_identifiers(coverage, coverage_index)
    for order_index, observation_order in enumerate(message.observation_orders):
        for identifier_index, identifier in enumerate(observation_order.identifiers):
            yield (
                f"observation_orders[{order_index}].identifiers[{identifier_index}]",
                identifier,
            )
    for order_index, medication_order in enumerate(message.medication_orders):
        for identifier_index, identifier in enumerate(medication_order.identifiers):
            yield (
                f"medication_orders[{order_index}].identifiers[{identifier_index}]",
                identifier,
            )


def iter_codings(message: CanonicalClinicalMessage) -> Iterator[tuple[str, Coding]]:
    """Yield canonical coded concepts with stable structural paths."""

    for index, diagnosis in enumerate(message.diagnoses):
        yield from _diagnosis_codings(diagnosis, index)
    for index, allergy in enumerate(message.allergies):
        yield from _allergy_codings(allergy, index)
    for index, observation_order in enumerate(message.observation_orders):
        yield from _observation_order_codings(observation_order, index)
    for index, coverage in enumerate(message.coverages):
        yield from _coverage_codings(coverage, index)
    for index, medication_order in enumerate(message.medication_orders):
        yield from _medication_order_codings(medication_order, index)
    for index, administration in enumerate(message.medication_administrations):
        yield from _medication_administration_codings(administration, index)


def _coverage_identifiers(
    coverage: Coverage,
    coverage_index: int,
) -> Iterator[tuple[str, Identifier]]:
    groups = (
        ("policy_identifiers", coverage.policy_identifiers),
        ("payer_identifiers", coverage.payer_identifiers),
        ("subscriber_identifiers", coverage.subscriber_identifiers),
    )
    for group_name, identifiers in groups:
        for identifier_index, identifier in enumerate(identifiers):
            yield (
                f"coverages[{coverage_index}].{group_name}[{identifier_index}]",
                identifier,
            )


def _diagnosis_codings(
    diagnosis: Diagnosis,
    index: int,
) -> Iterator[tuple[str, Coding]]:
    yield f"diagnoses[{index}].code", diagnosis.code


def _allergy_codings(allergy: Allergy, index: int) -> Iterator[tuple[str, Coding]]:
    yield f"allergies[{index}].allergen", allergy.allergen
    if allergy.category is not None:
        yield f"allergies[{index}].category", allergy.category
    if allergy.severity is not None:
        yield f"allergies[{index}].severity", allergy.severity


def _observation_order_codings(
    order: ObservationOrder,
    order_index: int,
) -> Iterator[tuple[str, Coding]]:
    yield f"observation_orders[{order_index}].service", order.service
    for reason_index, reason in enumerate(order.reasons):
        yield f"observation_orders[{order_index}].reasons[{reason_index}]", reason
    for result_index, result in enumerate(order.results):
        yield from _observation_codings(result, order_index, result_index)


def _observation_codings(
    observation: Observation,
    order_index: int,
    result_index: int,
) -> Iterator[tuple[str, Coding]]:
    prefix = f"observation_orders[{order_index}].results[{result_index}]"
    yield f"{prefix}.code", observation.code
    if observation.units is not None:
        yield f"{prefix}.units", observation.units
    for method_index, method in enumerate(observation.methods):
        yield f"{prefix}.methods[{method_index}]", method


def _coverage_codings(
    coverage: Coverage,
    index: int,
) -> Iterator[tuple[str, Coding]]:
    if coverage.plan is not None:
        yield f"coverages[{index}].plan", coverage.plan
    if coverage.relationship is not None:
        yield f"coverages[{index}].relationship", coverage.relationship


def _route_codings(
    route: MedicationRoute,
    prefix: str,
) -> Iterator[tuple[str, Coding]]:
    yield f"{prefix}.route", route.route
    if route.site is not None:
        yield f"{prefix}.site", route.site
    if route.method is not None:
        yield f"{prefix}.method", route.method
    if route.device is not None:
        yield f"{prefix}.device", route.device


def _medication_order_codings(
    order: MedicationOrder,
    index: int,
) -> Iterator[tuple[str, Coding]]:
    prefix = f"medication_orders[{index}]"
    yield f"{prefix}.medication", order.medication
    if order.strength_unit is not None:
        yield f"{prefix}.strength_unit", order.strength_unit
    for instruction_index, instruction in enumerate(order.instructions):
        yield f"{prefix}.instructions[{instruction_index}]", instruction
    for route_index, route in enumerate(order.routes):
        yield from _route_codings(route, f"{prefix}.routes[{route_index}]")


def _medication_administration_codings(
    administration: MedicationAdministration,
    index: int,
) -> Iterator[tuple[str, Coding]]:
    prefix = f"medication_administrations[{index}]"
    yield f"{prefix}.medication", administration.medication
    optional = (
        ("manufacturer", administration.manufacturer),
        ("refusal_reason", administration.refusal_reason),
        ("indication", administration.indication),
    )
    for field_name, coding in optional:
        if coding is not None:
            yield f"{prefix}.{field_name}", coding
    for route_index, route in enumerate(administration.routes):
        yield from _route_codings(route, f"{prefix}.routes[{route_index}]")
