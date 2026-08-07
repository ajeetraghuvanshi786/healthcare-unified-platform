from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.common_order import CommonOrder
from healthcare_pipeline.parsers.hl7.observation_request import ObservationRequest
from healthcare_pipeline.parsers.hl7.observation_result import ObservationResult


@dataclass(frozen=True, slots=True)
class ObservationOrderGroup:
    """One OBR request and its associated ORC context and OBX results."""

    request: ObservationRequest
    results: tuple[ObservationResult, ...] = ()
    common_order: CommonOrder | None = None
    source_segment_sequences: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, ObservationRequest):
            raise TypeError("request must be an ObservationRequest")
        if self.common_order is not None and not isinstance(self.common_order, CommonOrder):
            raise TypeError("common_order must be a CommonOrder or None")

        results = tuple(self.results)
        if not all(isinstance(value, ObservationResult) for value in results):
            raise TypeError("results must contain only ObservationResult values")
        object.__setattr__(self, "results", results)

        sequences = tuple(self.source_segment_sequences)
        if not sequences:
            raise ValueError("source_segment_sequences must not be empty")
        if any(not isinstance(value, int) or value < 1 for value in sequences):
            raise ValueError("source_segment_sequences must contain positive integers")
        if sequences != tuple(sorted(set(sequences))):
            raise ValueError("source_segment_sequences must be unique and increasing")
        object.__setattr__(self, "source_segment_sequences", sequences)

    @property
    def has_results(self) -> bool:
        """Return whether at least one OBX result belongs to this OBR."""

        return bool(self.results)
