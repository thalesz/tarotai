# script-build-push.ps1

param(
    [string]$ImageLocalName = "tarotai-backend",
    [string]$ImageRemoteName = "thalesz/tarotai-backend:latest",
    [string]$EnvFile = ".env",
    [string]$PostgresUrl,
    [switch]$UseEnvHash
)

# Variáveis
$imageLocalName = $ImageLocalName
$imageRemoteName = $ImageRemoteName

# Opcional: calcular hash do .env para forçar rebuild de cache sem vazar segredos
$buildExtraArgs = @()
if ($UseEnvHash -and (Test-Path $EnvFile)) {
    try {
        $envHash = (Get-FileHash -Path $EnvFile -Algorithm SHA256).Hash.ToLower()
        Write-Host "Usando env hash para cache bust: $envHash" -ForegroundColor DarkGray
        $buildExtraArgs += @('--label', "env-hash=$envHash")
    } catch {
        Write-Host "Falha ao calcular hash do env. Prosseguindo sem label." -ForegroundColor Yellow
    }
} elseif ($UseEnvHash) {
    Write-Host "Arquivo de env não encontrado: $EnvFile. Prosseguindo sem label." -ForegroundColor Yellow
}

# Remove a imagem local, se existir
Write-Host "Removendo imagem local $imageLocalName se existir..." -ForegroundColor Yellow
docker image rm $imageLocalName -f 2>$null

# Build da imagem
Write-Host "Construindo a imagem local $imageLocalName..." -ForegroundColor Cyan

# Coletar build-args a partir do arquivo .env (simples e direto)
$buildArgPairs = @()
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $m = [regex]::Match($line, '^([A-Za-z0-9_]+)\s*=\s*(.*)$')
        if ($m.Success) {
            $key = $m.Groups[1].Value
            $val = $m.Groups[2].Value
            # Remover aspas envolventes
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            # Sobrescrever POSTGRES_URL se foi fornecido parâmetro
            if ($key -eq 'POSTGRES_URL' -and -not [string]::IsNullOrEmpty($PostgresUrl)) {
                Write-Host "Substituindo POSTGRES_URL (via parâmetro)..." -ForegroundColor Yellow
                $val = $PostgresUrl
            }
            # Adicionar como build-arg (um par de args para cada chave)
            $buildArgPairs += @('--build-arg', "$key=$val")
        }
    }
} else {
    Write-Host "Arquivo .env não encontrado: $EnvFile. Prosseguindo sem build-args." -ForegroundColor Yellow
}

docker build @buildExtraArgs @buildArgPairs -t $imageLocalName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao construir a imagem!" -ForegroundColor Red
    exit 1
}

# Tag para Docker Hub
Write-Host "Tagueando a imagem para $imageRemoteName..." -ForegroundColor Cyan
docker tag $imageLocalName $imageRemoteName

# Push para o Docker Hub
Write-Host "Enviando a imagem para o Docker Hub..." -ForegroundColor Cyan
docker push $imageRemoteName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao enviar a imagem para o Docker Hub!" -ForegroundColor Red
    exit 1
}

Write-Host "Pronto! Imagem atualizada no Docker Hub." -ForegroundColor Green
Write-Host "Imagem disponível em: $imageRemoteName" -ForegroundColor Green
