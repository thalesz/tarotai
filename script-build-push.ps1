# script-build-push.ps1

# Variáveis
$imageLocalName = "tarotai-backend"
$imageRemoteName = "thalesz/tarotai-backend:latest"

# Remove a imagem local, se existir
Write-Host "Removendo imagem local $imageLocalName se existir..." -ForegroundColor Yellow
docker image rm $imageLocalName -f 2>$null

# Build da imagem
Write-Host "Construindo a imagem local $imageLocalName..." -ForegroundColor Cyan
docker build -t $imageLocalName .

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
