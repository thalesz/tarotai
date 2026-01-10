# azure-config-webapp.ps1
param(
    [Parameter(Mandatory=$true)][string]$ResourceGroup,
    [Parameter(Mandatory=$true)][string]$WebAppName,
    [string]$ImageName = "thalesz/tarotai-backend:latest",
    [string]$EnvFile = ".env",
    [switch]$CreateIfMissing,
    [string]$Location = "canadacentral"
)

Write-Host "Configuring Azure Web App to use container $ImageName..." -ForegroundColor Cyan

# Check Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Azure CLI (az) is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Ensure logged in
$account = az account show 2>$null | Out-String
if (-not $account) {
    Write-Host "You are not logged in. Launching az login..." -ForegroundColor Yellow
    az login | Out-Null
}

# Optionally create the Web App if missing (Linux, container)
$exists = az webapp show -g $ResourceGroup -n $WebAppName 2>$null | Out-String
if (-not $exists -and $CreateIfMissing) {
    Write-Host "Creating App Service Plan and Web App (Linux, container)..." -ForegroundColor Yellow
    $planName = "$WebAppName-plan"
    az appservice plan create -g $ResourceGroup -n $planName --sku B1 --is-linux --location $Location | Out-Null
    az webapp create -g $ResourceGroup -p $planName -n $WebAppName --runtime "PYTHON:3.12" --location $Location | Out-Null
}

# Set container image
az webapp config container set -g $ResourceGroup -n $WebAppName --docker-custom-image-name $ImageName | Out-Null

# Build app settings from .env
if (-not (Test-Path $EnvFile)) {
    Write-Host "Env file not found: $EnvFile" -ForegroundColor Red
    exit 1
}

$settings = @()
$settings += "WEBSITES_PORT=8000"

Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { return }
    $m = [regex]::Match($line, '^([A-Za-z0-9_]+)\s*=\s*(.*)$')
    if ($m.Success) {
        $key = $m.Groups[1].Value
        $val = $m.Groups[2].Value
        # Strip surrounding quotes
        if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        $settings += "$key=$val"
    }
}

Write-Host "Applying App Settings (including WEBSITES_PORT) ..." -ForegroundColor Cyan
az webapp config appsettings set -g $ResourceGroup -n $WebAppName --settings $settings | Out-Null

# Restart Web App
Write-Host "Restarting Web App..." -ForegroundColor Cyan
az webapp restart -g $ResourceGroup -n $WebAppName | Out-Null

Write-Host "Done. Container configured and App Settings applied." -ForegroundColor Green
