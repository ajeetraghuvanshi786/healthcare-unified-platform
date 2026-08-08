from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class Provider:
    """Source-preserving provider identity from the HL7 XCN datatype."""

    identifier: str | None = None
    family_name: str | None = None
    given_name: str | None = None
    middle_name: str | None = None
    suffix: str | None = None
    prefix: str | None = None
    professional_degree: str | None = None
    source_table: str | None = None
    assigning_authority: str | None = None
    name_type: str | None = None
    identifier_type: str | None = None

    def __post_init__(self) -> None:
        fields = (
            "identifier",
            "family_name",
            "given_name",
            "middle_name",
            "suffix",
            "prefix",
            "professional_degree",
            "source_table",
            "assigning_authority",
            "name_type",
            "identifier_type",
        )
        for field_name in fields:
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if self.identifier is None and self.family_name is None and self.given_name is None:
            raise ValueError("provider must include an identifier or name")

    @property
    def identity_key(self) -> tuple[str | None, str | None, str | None]:
        return (
            self.assigning_authority.casefold()
            if self.assigning_authority is not None
            else None,
            self.identifier,
            self.identifier_type.upper()
            if self.identifier_type is not None
            else None,
        )
