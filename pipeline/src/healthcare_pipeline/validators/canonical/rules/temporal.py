from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class EncounterTemporalRule:
    """Check clinical timestamps against a known encounter window without over-rejecting."""

    rule_id: str = "canonical.encounter-temporal"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        if message.encounter is None or message.encounter.period is None:
            return ()
        period = message.encounter.period
        if period.start is None and period.end is None:
            return ()

        issues: list[ValidationIssue] = []
        for order_index, order in enumerate(message.observation_orders):
            for result_index, observation in enumerate(order.results):
                self._append_if_outside(
                    issues,
                    observation.effective_datetime,
                    period.start,
                    period.end,
                    f"observation_orders[{order_index}].results[{result_index}].effective_datetime",
                )
        for index, administration in enumerate(message.medication_administrations):
            self._append_if_outside(
                issues,
                administration.start_datetime,
                period.start,
                period.end,
                f"medication_administrations[{index}].start_datetime",
            )
        return tuple(issues)

    def _append_if_outside(
        self,
        issues: list[ValidationIssue],
        value: datetime | None,
        start: datetime | None,
        end: datetime | None,
        path: str,
    ) -> None:
        if value is None:
            return
        if (start is not None and value < start) or (end is not None and value > end):
            issues.append(
                ValidationIssue(
                    code="CLINICAL_TIME_OUTSIDE_ENCOUNTER",
                    message=(
                        "Clinical timestamp falls outside the known encounter period; "
                        "verify source timing and encounter association."
                    ),
                    severity=ValidationSeverity.WARNING,
                    path=path,
                    rule_id=self.rule_id,
                )
            )
