from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common.quantity import Quantity
from healthcare_pipeline.canonical.medication.order import MedicationOrder
from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class MedicationDoseRule:
    """Apply source-neutral consistency checks to medication dose information."""

    rule_id: str = "canonical.medication-dose"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for index, order in enumerate(message.medication_orders):
            issues.extend(self._validate_order(order, index))
        for index, administration in enumerate(message.medication_administrations):
            if administration.amount.unit is None:
                issues.append(
                    ValidationIssue(
                        code="ADMINISTRATION_UNIT_MISSING",
                        message=(
                            "Medication administration amount has no unit; dose "
                            "interpretation may be unsafe."
                        ),
                        severity=ValidationSeverity.WARNING,
                        path=f"medication_administrations[{index}].amount.unit",
                        rule_id=self.rule_id,
                    )
                )
        return tuple(issues)

    def _validate_order(
        self,
        order: MedicationOrder,
        index: int,
    ) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        minimum = order.dose_minimum
        maximum = order.dose_maximum
        if minimum is not None and maximum is not None:
            if self._same_unit(minimum, maximum) and minimum.value > maximum.value:
                issues.append(
                    ValidationIssue(
                        code="DOSE_RANGE_REVERSED",
                        message="Medication minimum dose exceeds maximum dose.",
                        severity=ValidationSeverity.ERROR,
                        path=f"medication_orders[{index}]",
                        rule_id=self.rule_id,
                    )
                )
            elif not self._same_unit(minimum, maximum):
                issues.append(
                    ValidationIssue(
                        code="DOSE_RANGE_UNIT_MISMATCH",
                        message=(
                            "Minimum and maximum doses use different or incomplete units; "
                            "the range cannot be compared safely."
                        ),
                        severity=ValidationSeverity.WARNING,
                        path=f"medication_orders[{index}]",
                        rule_id=self.rule_id,
                    )
                )
        if order.strength is not None and order.strength_unit is None:
            issues.append(
                ValidationIssue(
                    code="MEDICATION_STRENGTH_UNIT_MISSING",
                    message="Medication strength is present without a strength unit.",
                    severity=ValidationSeverity.WARNING,
                    path=f"medication_orders[{index}].strength_unit",
                    rule_id=self.rule_id,
                )
            )
        return tuple(issues)

    @staticmethod
    def _same_unit(left: Quantity, right: Quantity) -> bool:
        if left.unit is None or right.unit is None:
            return False
        return left.unit.key == right.unit.key
