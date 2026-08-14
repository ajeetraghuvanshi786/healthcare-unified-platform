$ErrorActionPreference = "Stop"

$PipelineRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $PipelineRoot
$EnvPath = Join-Path $ProjectRoot ".env"
$ExamplePath = Join-Path $ProjectRoot ".env.example"
$LegacyPipelineEnv = Join-Path $PipelineRoot ".env"

if (-not (Test-Path $ExamplePath)) {
    throw "Missing $ExamplePath"
}

if (-not (Test-Path $EnvPath)) {
    Copy-Item $ExamplePath $EnvPath
}
else {
    Copy-Item $EnvPath "$EnvPath.backup" -Force
}

function New-Token([int]$Bytes) {
    return python -c "import secrets; print(secrets.token_urlsafe($Bytes))"
}

function New-HexKey([int]$Bytes) {
    return python -c "import secrets; print(secrets.token_hex($Bytes))"
}

function Is-UsableSecret([string]$Value, [int]$MinimumLength) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    if ($Value.StartsWith("<") -and $Value.EndsWith(">")) { return $false }
    return $Value.Length -ge $MinimumLength
}

$Existing = @{}
if (Test-Path $EnvPath) {
    foreach ($Line in Get-Content $EnvPath) {
        if ($Line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $Existing[$Matches[1]] = $Matches[2]
        }
    }
}

$ApiToken = $Existing["API_AUTH_TOKEN"]
if (-not (Is-UsableSecret $ApiToken 32)) {
    $ApiToken = New-Token 48
}

$HmacSecret = $Existing["IDENTITY_HMAC_SECRET"]
if (-not (Is-UsableSecret $HmacSecret 32)) {
    $HmacSecret = New-Token 48
}

$EncryptionKey = $Existing["IDENTITY_ENCRYPTION_KEY_HEX"]
if ($null -eq $EncryptionKey -or $EncryptionKey -notmatch '^[0-9A-Fa-f]{64}$') {
    $EncryptionKey = New-HexKey 32
}

$Required = [ordered]@{
    "POSTGRES_DB" = "healthcare_platform"
    "POSTGRES_USER" = "healthcare_user"
    "POSTGRES_PASSWORD" = "local_development_password"
    "POSTGRES_HOST" = "localhost"
    "POSTGRES_PORT" = "5433"
    "DATABASE_URL" = "postgresql+psycopg://healthcare_user:local_development_password@localhost:5433/healthcare_platform"
    "APP_ENV" = "local"
    "LOG_LEVEL" = "INFO"
    "API_AUTH_TOKEN" = $ApiToken
    "IDENTITY_HMAC_SECRET" = $HmacSecret
    "IDENTITY_ENCRYPTION_KEY_HEX" = $EncryptionKey
    "IDENTITY_ENCRYPTION_KEY_ID" = "local-v1"
    "API_HOST" = "127.0.0.1"
    "API_PORT" = "8000"
    "MAX_HL7_PAYLOAD_BYTES" = "2097152"
    "IDENTITY_MAX_CANDIDATES" = "100"
}

foreach ($Pair in $Required.GetEnumerator()) {
    $Existing[$Pair.Key] = [string]$Pair.Value
}

$Order = @(
    "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT",
    "DATABASE_URL", "APP_ENV", "LOG_LEVEL", "API_AUTH_TOKEN", "IDENTITY_HMAC_SECRET",
    "IDENTITY_ENCRYPTION_KEY_HEX", "IDENTITY_ENCRYPTION_KEY_ID", "API_HOST", "API_PORT",
    "MAX_HL7_PAYLOAD_BYTES", "IDENTITY_MAX_CANDIDATES"
)

$Output = New-Object System.Collections.Generic.List[string]
foreach ($Key in $Order) {
    $Output.Add("$Key=$($Existing[$Key])")
}
foreach ($Key in ($Existing.Keys | Sort-Object)) {
    if ($Order -notcontains $Key) {
        $Output.Add("$Key=$($Existing[$Key])")
    }
}

$Output | Set-Content -Path $EnvPath -Encoding utf8

if (Test-Path $LegacyPipelineEnv) {
    $LegacyPath = Join-Path $PipelineRoot ".env.legacy"
    Move-Item $LegacyPipelineEnv $LegacyPath -Force
    Write-Host "Renamed duplicate pipeline .env to .env.legacy"
}

Write-Host "Configured repository-root .env without printing secret values."
Write-Host "Existing valid identity secrets were preserved to avoid breaking encrypted records."
Write-Host "Database target: localhost:5433 / healthcare_platform"
