from __future__ import annotations

from dataclasses import dataclass, field

from healthcare_pipeline.canonical.traversal import iter_codings
from healthcare_pipeline.canonical.workflow.clinical_message import CanonicalClinicalMessage
from healthcare_pipeline.terminology.models import CodingAssessment
from healthcare_pipeline.terminology.service import TerminologyService


@dataclass(slots=True)
class CanonicalTerminologyService:
    """Apply terminology normalization/validation to all coded canonical concepts."""

    terminology: TerminologyService = field(default_factory=TerminologyService)
    max_assessments: int = 4096

    def __post_init__(self) -> None:
        if isinstance(self.max_assessments, bool) or not isinstance(self.max_assessments, int):
            raise TypeError("max_assessments must be an integer")
        if self.max_assessments < 1:
            raise ValueError("max_assessments must be greater than zero")

    def assess_message(
        self,
        message: CanonicalClinicalMessage,
    ) -> tuple[CodingAssessment, ...]:
        if not isinstance(message, CanonicalClinicalMessage):
            raise TypeError("message must be a CanonicalClinicalMessage")
        assessments: list[CodingAssessment] = []
        for path, coding in iter_codings(message):
            if len(assessments) >= self.max_assessments:
                break
            assessments.append(
                CodingAssessment(
                    path=path,
                    normalized=self.terminology.normalize(coding),
                    validation=self.terminology.validate(coding),
                )
            )
        return tuple(assessments)
