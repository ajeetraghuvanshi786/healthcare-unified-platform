from healthcare_pipeline.terminology import (
    LOINC,
    CodeValidationResult,
    CodeValidationStatus,
    StaticTerminologyProvider,
    TerminologyValidationCache,
)


def test_bounded_cache_evicts_least_recently_used_entry() -> None:
    cache = TerminologyValidationCache(max_entries=2)
    result = CodeValidationResult(status=CodeValidationStatus.VALID)
    first = (LOINC.canonical_uri, "A", None, "provider")
    second = (LOINC.canonical_uri, "B", None, "provider")
    third = (LOINC.canonical_uri, "C", None, "provider")

    cache.put(first, result)
    cache.put(second, result)
    assert cache.get(first) == result
    cache.put(third, result)

    assert cache.get(second) is None
    assert cache.get(first) == result
    assert cache.get(third) == result


def test_static_provider_rejects_code_not_in_curated_set() -> None:
    provider = StaticTerminologyProvider(
        name="local-loinc",
        code_sets={LOINC.canonical_uri: frozenset({"718-7"})},
    )

    result = provider.validate_code(
        system_uri=LOINC.canonical_uri,
        code="UNKNOWN",
        version=None,
    )

    assert result.status is CodeValidationStatus.INVALID
    assert "UNKNOWN" not in (result.message or "")
