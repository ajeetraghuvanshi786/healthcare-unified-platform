import healthcare_pipeline.identity as identity


def test_identity_public_api_is_resolvable() -> None:
    expected = {
        "DeterministicPatientMatcher",
        "HmacIdentityKeyEncoder",
        "IdentityCandidateStore",
        "IdentityRecord",
        "IdentityResolutionResult",
        "IdentityResolutionStatus",
        "IdentityScope",
        "InMemoryIdentityCandidateStore",
        "PatientIdentityResolver",
        "PatientIdentityService",
    }
    assert expected.issubset(set(identity.__all__))
    for name in expected:
        assert getattr(identity, name) is not None
