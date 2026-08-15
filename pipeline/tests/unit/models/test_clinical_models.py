import healthcare_pipeline.models as models
from healthcare_pipeline.models.base import Base


def test_phase_4a_clinical_tables_are_registered() -> None:
    assert models.ClinicalMessageRecord.__tablename__ == "clinical_messages"
    required = {
        "clinical_messages",
        "clinical_encounters",
        "clinical_diagnoses",
        "clinical_observations",
        "clinical_allergies",
        "clinical_medication_orders",
        "clinical_medication_administrations",
        "clinical_coverages",
        "clinical_provenance",
        "clinical_timeline_events",
    }
    assert required <= set(Base.metadata.tables)


def test_database_identifiers_fit_postgresql_limit() -> None:
    oversized: list[str] = []
    for table in Base.metadata.sorted_tables:
        for item in list(table.constraints) + list(table.indexes):
            name = item.name
            if name is not None and len(name) > 63:
                oversized.append(name)
    assert oversized == []
