from healthcare_pipeline.canonical import Coding
from healthcare_pipeline.terminology import (
    LOINC,
    CodeValidationStatus,
    StaticTerminologyProvider,
    TerminologyResolutionStatus,
    TerminologyService,
)


def test_service_normalizes_known_alias_without_mutating_source() -> None:
    source = Coding(code="718-7", display="Hemoglobin", system="LN")

    result = TerminologyService().normalize(source)

    assert source.system == "LN"
    assert result.coding.system == LOINC.canonical_uri
    assert result.status is TerminologyResolutionStatus.NORMALIZED
    assert result.system is LOINC


def test_service_preserves_unknown_or_missing_systems() -> None:
    service = TerminologyService()

    unknown = service.normalize(Coding(code="ABC", system="LOCAL-LAB"))
    missing = service.normalize(Coding(display="Local textual concept"))

    assert unknown.status is TerminologyResolutionStatus.UNKNOWN_SYSTEM
    assert unknown.coding.system == "LOCAL-LAB"
    assert missing.status is TerminologyResolutionStatus.MISSING_SYSTEM


def test_service_validates_with_static_provider_and_caches_result() -> None:
    provider = StaticTerminologyProvider(
        name="local-loinc",
        code_sets={LOINC.canonical_uri: frozenset({"718-7"})},
    )
    service = TerminologyService(providers=(provider,))
    coding = Coding(code="718-7", system="LN")

    first = service.validate(coding)
    second = service.validate(coding)

    assert first.status is CodeValidationStatus.VALID
    assert second == first
    assert service.cache.size == 1


def test_service_returns_safe_status_when_no_provider_is_configured() -> None:
    result = TerminologyService().validate(Coding(code="718-7", system="LN"))

    assert result.status is CodeValidationStatus.NOT_CHECKED
    assert result.provider_name is None
