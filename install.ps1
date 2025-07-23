function Write-Color($Text, $Color) { Write-Host $Text -ForegroundColor $Color }

Write-Color "==> Checking for Docker..." Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Color "Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/ and rerun this script." Red
    exit 1
} else {
    Write-Color "Docker is already installed." Green
}

Write-Color "==> Checking for Docker Compose..." Cyan
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Color "Docker Compose not found. It should be included with Docker Desktop. Please ensure Docker Desktop is up to date." Yellow
    exit 1
} else {
    Write-Color "Docker Compose is already installed." Green
}

Write-Color "==> Building the app Docker image locally..." Cyan
docker build -t gemma3n-app:latest .

Write-Color "==> Building and starting all services..." Cyan
docker-compose up -d --build

Write-Color "==> Waiting for services to become healthy..." Cyan
while ((docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>$null) -ne "healthy") {
    Write-Color "Waiting for app to be healthy..." Yellow
    Start-Sleep -Seconds 5
}

Write-Color "==> All services are running and healthy!" Green
Write-Color "==> Access the app at http://localhost:8050" Cyan 