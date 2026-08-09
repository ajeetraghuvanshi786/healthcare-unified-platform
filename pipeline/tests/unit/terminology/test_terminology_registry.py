import pytest

from healthcare_pipeline.terminology import (
    DEFAULT_TERMINOLOGY_REGISTRY,
    ICD10_CM,
    LOINC,
    RXNORM,
    SNOMED_CT,
    UCUM,
)


def test_registry_resolves_hl7_aliases_oids_and_canonical_uris() -> None:
    registry = DEFAULT_TERMINOLOGY_REGISTRY

    assert registry.resolve("LN") is LOINC
    assert registry.resolve("loinc") is LOINC
    assert registry.resolve("urn:oid:2.16.840.1.113883.6.96") is SNOMED_CT
    assert registry.resolve(RXNORM.canonical_uri) is RXNORM
    assert registry.resolve("UCUM") is UCUM
    assert registry.resolve("http://terminology.hl7.org/CodeSystem/icd10CM") is ICD10_CM


def test_registry_does_not_case_fold_uri_identifiers() -> None:
    registry = DEFAULT_TERMINOLOGY_REGISTRY

    assert registry.resolve("HTTP://LOINC.ORG") is None


def test_registry_rejects_blank_identifier_type_safely() -> None:
    registry = DEFAULT_TERMINOLOGY_REGISTRY

    assert registry.resolve("  ") is None
    with pytest.raises(TypeError, match="string"):
        registry.resolve(123)  # type: ignore[arg-type]
