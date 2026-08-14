$ErrorActionPreference = "Stop"

$PipelineRoot = Split-Path -Parent $PSScriptRoot
Set-Location $PipelineRoot

Write-Host "=== Python ==="
python -c "import sys; print(sys.executable); print(sys.version)"

Write-Host "=== Configuration ==="
python -c @'
from healthcare_pipeline.config.settings import ENV_FILE, get_settings
from sqlalchemy.engine import make_url
s = get_settings()
u = make_url(s.database_url)
s.require_api_auth_token()
s.require_identity_hmac_secret()
s.require_identity_encryption_key()
print('ENV_FILE:', ENV_FILE)
print('database_host:', u.host)
print('database_port:', u.port)
print('database_name:', u.database)
print('security_configuration: OK')
'@

Write-Host "=== Static quality ==="
ruff check src tests
mypy src/healthcare_pipeline

Write-Host "=== Phase 3H ==="
pytest tests/unit/identity/persistence -q
pytest tests/unit/identity/master -q
pytest tests/unit/identity -q

Write-Host "=== Phase 3I ==="
pytest tests/unit/application -q

Write-Host "=== Phase 3J ==="
pytest tests/unit/api -q

Write-Host "=== Unit regression ==="
pytest tests/unit -q

Write-Host "=== Database connection ==="
pytest tests/test_database_connection.py -q

Write-Host "=== Alembic discovery ==="
alembic -c .\alembic.ini history
alembic -c .\alembic.ini heads
alembic -c .\alembic.ini current

Write-Host "Validation complete. Apply 'alembic upgrade head' only after reviewing current state."
