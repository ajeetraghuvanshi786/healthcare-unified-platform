from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from healthcare_pipeline.terminology.models import TerminologySystem
from healthcare_pipeline.terminology.systems import DEFAULT_TERMINOLOGY_SYSTEMS


def _identifier_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("terminology identifier must not be blank")
    if normalized.casefold().startswith(("http://", "https://", "urn:")):
        return normalized
    return normalized.casefold()


@dataclass(frozen=True, slots=True)
class TerminologyRegistry:
    """Immutable lookup registry for authoritative systems and local aliases."""

    systems: tuple[TerminologySystem, ...] = DEFAULT_TERMINOLOGY_SYSTEMS
    _lookup: Mapping[str, TerminologySystem] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        systems = tuple(self.systems)
        lookup: dict[str, TerminologySystem] = {}
        for system in systems:
            identifiers = [system.canonical_uri, *system.aliases]
            if system.oid is not None:
                identifiers.extend((system.oid, f"urn:oid:{system.oid}"))
            for identifier in identifiers:
                key = _identifier_key(identifier)
                existing = lookup.get(key)
                if existing is not None and existing != system:
                    raise ValueError("terminology identifier is registered more than once")
                lookup[key] = system
        object.__setattr__(self, "systems", systems)
        object.__setattr__(self, "_lookup", MappingProxyType(lookup))

    def resolve(self, identifier: str) -> TerminologySystem | None:
        """Resolve a URI, OID, or configured short alias to one known system."""

        if not isinstance(identifier, str):
            raise TypeError("identifier must be a string")
        if not identifier.strip():
            return None
        return self._lookup.get(_identifier_key(identifier))


DEFAULT_TERMINOLOGY_REGISTRY = TerminologyRegistry()
