from enum import StrEnum


class ValidationSeverity(StrEnum):
    """Severity assigned to a source-neutral canonical validation issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

    @property
    def blocks_processing(self) -> bool:
        return self in {ValidationSeverity.ERROR, ValidationSeverity.FATAL}
