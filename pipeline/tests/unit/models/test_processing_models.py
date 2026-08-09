from healthcare_pipeline.models import (
    DeadLetterRecord,
    ProcessingCheckpoint,
    ProcessingJob,
    TransformationLog,
    ValidationResult,
)


def test_phase_2c2_table_names() -> None:
    assert ProcessingJob.__tablename__ == "processing_job"
    assert ValidationResult.__tablename__ == "validation_result"
    assert TransformationLog.__tablename__ == "transformation_log"
    assert DeadLetterRecord.__tablename__ == "dead_letter_record"
    assert ProcessingCheckpoint.__tablename__ == "processing_checkpoint"


def test_processing_job_contains_orchestration_columns() -> None:
    columns = set(ProcessingJob.__table__.columns.keys())
    expected = {
        "tenant_id",
        "ingestion_batch_id",
        "raw_ingestion_record_id",
        "correlation_id",
        "stage",
        "status",
        "attempt_number",
        "max_attempts",
        "available_at",
        "lease_expires_at",
        "version",
    }
    assert expected.issubset(columns)


def test_validation_result_contains_audit_columns() -> None:
    columns = set(ValidationResult.__table__.columns.keys())
    expected = {
        "processing_job_id",
        "raw_ingestion_record_id",
        "category",
        "outcome",
        "severity",
        "rule_code",
        "message",
        "validated_at",
    }
    assert expected.issubset(columns)


def test_transformation_log_contains_lineage_columns() -> None:
    columns = set(TransformationLog.__table__.columns.keys())
    expected = {
        "processing_job_id",
        "sequence_number",
        "transformation_name",
        "transformation_version",
        "input_hash",
        "output_hash",
        "status",
    }
    assert expected.issubset(columns)


def test_dead_letter_record_contains_remediation_columns() -> None:
    columns = set(DeadLetterRecord.__table__.columns.keys())
    expected = {
        "raw_ingestion_record_id",
        "processing_job_id",
        "status",
        "recoverability",
        "failure_count",
        "next_retry_at",
        "resolved_at",
        "version",
    }
    assert expected.issubset(columns)


def test_processing_checkpoint_contains_resume_columns() -> None:
    columns = set(ProcessingCheckpoint.__table__.columns.keys())
    expected = {
        "source_system_id",
        "stage",
        "partition_key",
        "checkpoint_value",
        "last_processed_record_id",
        "watermark_at",
        "lease_expires_at",
        "version",
    }
    assert expected.issubset(columns)


def test_processing_foreign_keys_are_restrictive_or_nullable_safe() -> None:
    raw_record_fk = next(
        iter(ProcessingJob.__table__.columns["raw_ingestion_record_id"].foreign_keys)
    )
    dead_letter_job_fk = next(
        iter(DeadLetterRecord.__table__.columns["processing_job_id"].foreign_keys)
    )
    checkpoint_record_fk = next(
        iter(ProcessingCheckpoint.__table__.columns["last_processed_record_id"].foreign_keys)
    )

    assert raw_record_fk.ondelete == "RESTRICT"
    assert dead_letter_job_fk.ondelete == "SET NULL"
    assert checkpoint_record_fk.ondelete == "SET NULL"
