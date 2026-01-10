# script-run-local.ps1

param(
    [string]$ImageName = "thalesz/tarotai-backend:latest",
    [string]$EnvFile = ".env",
    [int]$Port = 8000,
    [switch]$Pull
)

Write-Host "Starting container with env from $EnvFile..." -ForegroundColor Cyan

if (-not (Test-Path $EnvFile)) {
    Write-Host "Env file not found: $EnvFile" -ForegroundColor Red
    exit 1
}

# Optionally pull latest image
if ($Pull) {
    Write-Host "Pulling image $ImageName..." -ForegroundColor Yellow
    docker pull $ImageName
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Stop/remove any existing container with same name
$containerName = "tarotai-backend"
$exists = docker ps -a --format '{{.Names}}' | Select-String -SimpleMatch $containerName
if ($exists) {
    Write-Host "Stopping and removing existing container $containerName..." -ForegroundColor Yellow
    docker stop $containerName 2>$null | Out-Null
    docker rm $containerName 2>$null | Out-Null
}

# Run container with env file
$runArgs = @(
    "run",
    "--rm",
    "--name", $containerName,
    "--env-file", $EnvFile,
    "-p", "$Port:8000",
    $ImageName
)

docker @runArgs
