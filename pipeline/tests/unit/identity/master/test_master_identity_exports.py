from healthcare_pipeline import identity


def test_master_identity_public_api_is_exported() -> None:
    required = {
        "MasterPatient",
        "MasterPatientLink",
        "ReviewCase",
        "IdentityDecisionEvent",
        "MasterPatientIdentityService",
        "InMemoryMasterIdentityRepository",
    }
    assert required.issubset(set(identity.__all__))
