from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.validators.canonical.issue import ValidationIssue
from healthcare_pipeline.validators.canonical.severity import ValidationSeverity


@dataclass(frozen=True, slots=True)
class ObservationQualityRule:
    """Validate result metadata needed for safe downstream interpretation."""

    rule_id: str = "canonical.observation-quality"

    def validate(self, message: CanonicalClinicalMessage) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for order_index, order in enumerate(message.observation_orders):
            if (
                order.observation_datetime is not None
                and order.requested_datetime is not None
                and order.observation_datetime < order.requested_datetime
            ):
                issues.append(
                    ValidationIssue(
                        code="OBSERVATION_PRECEDES_REQUEST",
                        message="Observation time precedes the request time.",
                        severity=ValidationSeverity.WARNING,
                        path=f"observation_orders[{order_index}].observation_datetime",
                        rule_id=self.rule_id,
                    )
                )
            for result_index, observation in enumerate(order.results):
                prefix = f"observation_orders[{order_index}].results[{result_index}]"
                if observation.value_type == "NM" and observation.units is None:
                    issues.append(
                        ValidationIssue(
                            code="NUMERIC_OBSERVATION_UNIT_MISSING",
                            message=(
                                "Numeric observation has no unit; downstream clinical "
                                "interpretation may be unsafe."
                            ),
                            severity=ValidationSeverity.WARNING,
                            path=f"{prefix}.units",
                            rule_id=self.rule_id,
                        )
                    )
        return tuple(issues)
