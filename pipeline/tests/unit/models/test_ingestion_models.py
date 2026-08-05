from healthcare_pipeline.models import (
    IngestionBatch,
    RawIngestionRecord,
)


def test_ingestion_batch_table_name() -> None:
    assert IngestionBatch.__tablename__ == "ingestion_batch"


def test_raw_ingestion_record_table_name() -> None:
    assert (
        RawIngestionRecord.__tablename__
        == "raw_ingestion_record"
    )


def test_ingestion_batch_contains_required_columns() -> None:
    columns = IngestionBatch.__table__.columns

    expected_columns = {
        "id",
        "tenant_id",
        "source_system_id",
        "batch_reference",
        "correlation_id",
        "transport",
        "data_standard",
        "status",
        "started_at",
        "created_at",
        "updated_at",
        "version",
    }

    assert expected_columns.issubset(set(columns.keys()))


def test_raw_record_contains_integrity_columns() -> None:
    columns = RawIngestionRecord.__table__.columns

    expected_columns = {
        "payload",
        "payload_hash",
        "payload_size_bytes",
        "idempotency_key",
        "received_at",
    }

    assert expected_columns.issubset(set(columns.keys()))


def test_raw_payload_is_required() -> None:
    payload_column = RawIngestionRecord.__table__.columns["payload"]

    assert payload_column.nullable is False


def test_raw_payload_hash_is_required() -> None:
    hash_column = RawIngestionRecord.__table__.columns["payload_hash"]

    assert hash_column.nullable is False