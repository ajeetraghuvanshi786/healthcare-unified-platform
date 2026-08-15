from __future__ import annotations

from sqlalchemy import inspect, text

from healthcare_pipeline.config.database import engine

_REQUIRED_TABLES = {
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


def main() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = sorted(_REQUIRED_TABLES - tables)
    if missing:
        raise SystemExit(f"Missing Phase 4 tables: {missing}")

    oversized: list[str] = []
    for table_name in sorted(_REQUIRED_TABLES):
        for index in inspector.get_indexes(table_name):
            name = index.get("name")
            if name and len(name) > 63:
                oversized.append(name)
        for foreign_key in inspector.get_foreign_keys(table_name):
            name = foreign_key.get("name")
            if name and len(name) > 63:
                oversized.append(name)
        for constraint in inspector.get_unique_constraints(table_name):
            name = constraint.get("name")
            if name and len(name) > 63:
                oversized.append(name)

    if oversized:
        raise SystemExit(f"PostgreSQL identifiers exceed 63 characters: {oversized}")

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    print("Phase 4 schema verification passed")
    print(f"alembic_revision={revision}")
    print(f"clinical_table_count={len(_REQUIRED_TABLES)}")
    print("postgresql_identifier_limit=verified")


if __name__ == "__main__":
    main()
