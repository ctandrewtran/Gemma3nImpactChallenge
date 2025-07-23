function Write-Color($Text, $Color) { Write-Host $Text -ForegroundColor $Color }

Write-Color "==> Checking for Docker..." Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Color "Docker not found. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/ and rerun this script." Red
    exit 1
} else {
    Write-Color "Docker is already installed." Green
}

# Check if Docker daemon is running
try {
    docker info | Out-Null
    Write-Color "Docker daemon is running." Green
} catch {
    Write-Color "Docker is installed, but the Docker daemon is not running. Please start Docker Desktop and rerun this script." Red
    exit 1
}

Write-Color "==> Checking for Docker Compose..." Cyan
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Color "Docker Compose not found. It should be included with Docker Desktop. Please ensure Docker Desktop is up to date." Yellow
    exit 1
} else {
    Write-Color "Docker Compose is already installed." Green
}

# Check for docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Color "docker-compose.yml not found in the current directory. Please make sure you are in the correct folder and the file exists." Red
    exit 1
}

Write-Color "==> Building the app Docker image locally..." Cyan
$buildResult = docker build -t gemma3n-app:latest . 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Color "Docker build failed with the following error:" Red
    Write-Color $buildResult Red
    exit 1
}

Write-Color "==> Building and starting all services..." Cyan
$composeResult = docker-compose up -d --build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Color "docker-compose up failed with the following error:" Red
    Write-Color $composeResult Red
    exit 1
}

Write-Color "==> Waiting for services to become healthy..." Cyan
$maxAttempts = 24
$attempt = 0
while ($attempt -lt $maxAttempts) {
    $status = docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>$null
    if ($status -eq "healthy") {
        Write-Color "==> All services are running and healthy!" Green
        Write-Color "==> Access the app at http://localhost:8050" Cyan
        exit 0
    }
    Write-Color "Waiting for app to be healthy..." Yellow
    Start-Sleep -Seconds 5
    $attempt++
}
Write-Color "App did not become healthy within 2 minutes. Please check Docker Desktop, logs, and try again." Red
exit 1 