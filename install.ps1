function Write-Color($Text, $Color) { Write-Host $Text -ForegroundColor $Color }

Write-Color "==> Checking for Docker and Docker Compose..." Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Color "Docker not found. Please install Docker." Red
    exit 1
}
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Color "Docker Compose not found. Please install Docker Compose." Red
    exit 1
}

Write-Color "==> Building and starting all services..." Cyan
docker-compose up -d --build

Write-Color "==> Waiting for services to become healthy..." Cyan
while ((docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>$null) -ne "healthy") {
    Write-Color "Waiting for app to be healthy..." Yellow
    Start-Sleep -Seconds 5
}

Write-Color "==> All services are running and healthy!" Green
Write-Color "==> Access the app at http://localhost:8050" Cyan 