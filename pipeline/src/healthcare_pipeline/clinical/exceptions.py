class ClinicalPersistenceError(RuntimeError):
    """Base error for durable clinical persistence failures."""


class ClinicalMessageConflict(ClinicalPersistenceError):
    """Same source message identity was reused for different canonical content."""
