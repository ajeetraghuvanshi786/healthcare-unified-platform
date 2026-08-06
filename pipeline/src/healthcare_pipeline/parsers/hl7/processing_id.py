from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HL7ProcessingMode(StrEnum):
    """Standard MSH-11 processing mode values."""

    PRODUCTION = "P"
    TRAINING = "T"
    DEBUGGING = "D"


@dataclass(frozen=True, slots=True)
class HL7ProcessingId:
    """Semantic representation of MSH-11 processing information."""

    mode: HL7ProcessingMode
    processing_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, HL7ProcessingMode):
            raise TypeError("mode must be an HL7ProcessingMode")
        if self.processing_version is not None:
            if not isinstance(self.processing_version, str):
                raise TypeError("processing_version must be a string or None")
            normalized = self.processing_version.strip()
            object.__setattr__(self, "processing_version", normalized or None)

    @classmethod
    def from_code(
        cls,
        code: str,
        *,
        processing_version: str | None = None,
    ) -> HL7ProcessingId:
        """Create a typed processing identifier from the MSH-11 code."""

        if not isinstance(code, str):
            raise TypeError("processing code must be a string")
        normalized = code.strip().upper()
        if not normalized:
            raise ValueError("processing code must not be blank")
        try:
            mode = HL7ProcessingMode(normalized)
        except ValueError as exc:
            raise ValueError(f"unsupported HL7 processing code: {normalized}") from exc
        return cls(mode=mode, processing_version=processing_version)
