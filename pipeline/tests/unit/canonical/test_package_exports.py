import healthcare_pipeline.canonical as canonical


def test_canonical_public_api_is_resolvable() -> None:
    names = (
        "Address",
        "AdministrativeGender",
        "Allergy",
        "CanonicalClinicalMessage",
        "Coding",
        "Coverage",
        "Diagnosis",
        "Encounter",
        "HumanName",
        "Identifier",
        "MedicationAdministration",
        "MedicationOrder",
        "Observation",
        "ObservationOrder",
        "Patient",
        "Provider",
        "Quantity",
    )
    assert all(hasattr(canonical, name) for name in names)
