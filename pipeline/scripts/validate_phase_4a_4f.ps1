$ErrorActionPreference = "Stop"

Write-Host "=== Phase 4A-4F configuration ==="
python -c "from healthcare_pipeline.config.settings import get_settings; s=get_settings(); print('database:', bool(s.database_url)); print('api auth:', s.api_auth_token is not None); print('hmac:', s.identity_hmac_secret is not None); print('encryption:', s.identity_encryption_key_hex is not None)"

Write-Host "`n=== Static quality ==="
ruff check src tests
mypy src/healthcare_pipeline

Write-Host "`n=== Phase 4 focused tests ==="
pytest tests/unit/clinical -v
pytest tests/unit/models/test_clinical_models.py -v
pytest tests/unit/api/test_processing_api.py -v

Write-Host "`n=== Full regression ==="
pytest -q

Write-Host "`n=== PostgreSQL identifier safety ==="
python -c "import healthcare_pipeline.models; from healthcare_pipeline.models.base import Base; bad=[(t.name,len(o.name),o.name) for t in Base.metadata.sorted_tables for o in list(t.constraints)+list(t.indexes) if o.name and len(o.name)>63]; print('oversized identifiers:', bad); raise SystemExit(1 if bad else 0)"

Write-Host "`n=== Alembic state ==="
alembic -c .\alembic.ini history
alembic -c .\alembic.ini heads
alembic -c .\alembic.ini current

Write-Host "`nPhase 4A-4F pre-E2E validation completed."
