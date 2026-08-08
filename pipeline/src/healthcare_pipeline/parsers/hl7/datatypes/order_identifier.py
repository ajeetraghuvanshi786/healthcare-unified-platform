from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional, normalize_required


@dataclass(frozen=True, slots=True)
class OrderIdentifier:
    """Source-preserving order identifier, typically from the EI datatype."""

    entity_identifier: str
    namespace_id: str | None = None
    universal_id: str | None = None
    universal_id_type: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entity_identifier",
            normalize_required(self.entity_identifier, "entity_identifier"),
        )
        for field_name in ("namespace_id", "universal_id", "universal_id_type"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )

    @property
    def identity_key(self) -> tuple[str | None, str, str | None]:
        return (
            self.namespace_id.casefold() if self.namespace_id is not None else None,
            self.entity_identifier,
            self.universal_id,
        )
