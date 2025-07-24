#!/usr/bin/env bash

# If you see a permission error, run this script with sudo:
# sudo bash install.sh

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

set -e

function pause_for_debug() {
    echo -e "${YELLOW}Press Enter to exit...${NC}"
    read
}

function install_docker_ubuntu() {
    echo -e "${CYAN}==> Installing Docker (Ubuntu)...${NC}"
    sudo apt-get update
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo -e "${GREEN}==> Docker installed. You may need to log out and back in for group changes to take effect.${NC}"
}

function install_docker_mac() {
    echo -e "${CYAN}==> Please install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop/ and rerun this script.${NC}"
    pause_for_debug
    exit 1
}

function install_docker_compose() {
    echo -e "${CYAN}==> Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}==> Docker Compose installed.${NC}"
}

echo -e "${CYAN}==> Checking for Docker...${NC}"
if ! command -v docker &> /dev/null; then
    OS=$(uname -s)
    if [[ "$OS" == "Linux" ]]; then
        install_docker_ubuntu
    elif [[ "$OS" == "Darwin" ]]; then
        install_docker_mac
    else
        echo -e "${RED}Unsupported OS: $OS. Please install Docker manually.${NC}"
        pause_for_debug
        exit 1
    fi
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# Check if Docker daemon is running
if ! sudo docker info &> /dev/null; then
    echo -e "${RED}Docker is installed, but the Docker daemon is not running. Please start Docker Desktop or the Docker service and rerun this script.${NC}"
    pause_for_debug
    exit 1
else
    echo -e "${GREEN}Docker daemon is running.${NC}"
fi

echo -e "${CYAN}==> Checking for Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    install_docker_compose
else
    echo -e "${GREEN}Docker Compose is already installed.${NC}"
fi

# Ensure git is installed before cloning
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Please install git (https://git-scm.com/download/) and rerun this script.${NC}"
    pause_for_debug
    exit 1
fi

# Clone the repo if docker-compose.yml is not present
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${CYAN}docker-compose.yml not found. Cloning the repository into a temporary folder...${NC}"
    tmpDir="AgenticRagForRuralGov_tmp"
    rm -rf "$tmpDir"
    git clone https://github.com/ctandrewtran/Gemma3nImpactChallenge.git "$tmpDir"
    if [ ! -f "$tmpDir/docker-compose.yml" ]; then
        echo -e "${RED}Failed to clone the repository or docker-compose.yml not found in the temp folder.${NC}"
        pause_for_debug
        exit 1
    fi
    # Move all files except .git from temp to current directory
    shopt -s dotglob
    for f in "$tmpDir"/*; do
        [ "$(basename "$f")" = ".git" ] && continue
        if [ -e "./$(basename "$f")" ]; then rm -rf "./$(basename "$f")"; fi
        mv "$f" .
    done
    shopt -u dotglob
    rm -rf "$tmpDir"
    echo -e "${GREEN}Repository files moved to current directory.${NC}"
    # Print and log the full path of the current directory
    fullPath="$(pwd)"
    echo -e "${CYAN}Current installation directory: $fullPath${NC}"
    echo "Installation directory: $fullPath" >> install.log
    # cd into the current directory (redundant, but explicit)
    cd "$fullPath"
fi

echo -e "${CYAN}==> Building the app Docker image locally...${NC}"
buildResult=$(sudo docker build -t gemma3n-app:latest . 2>&1)
buildCode=$?
if [ $buildCode -ne 0 ]; then
    echo -e "${RED}Docker build failed with the following error:${NC}"
    echo -e "${RED}$buildResult${NC}"
    pause_for_debug
    exit 1
fi

echo -e "${CYAN}==> Building and starting all services...${NC}"
composeResult=$(sudo docker-compose up -d --build 2>&1)
composeCode=$?
if [ $composeCode -ne 0 ]; then
    echo -e "${RED}docker-compose up failed with the following error:${NC}"
    echo -e "${RED}$composeResult${NC}"
    pause_for_debug
    exit 1
fi

echo -e "${CYAN}==> Waiting for services to become healthy...${NC}"
max_attempts=24
attempt=0
while [[ $attempt -lt $max_attempts ]]; do
    status=$(sudo docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>/dev/null)
    if [[ "$status" == "healthy" ]]; then
        echo -e "${GREEN}==> All services are running and healthy!${NC}"
        echo -e "${CYAN}==> Access the app at http://localhost:8050${NC}"
        exit 0
    fi
    echo -e "${YELLOW}Waiting for app to be healthy...${NC}"
    sleep 5
    attempt=$((attempt+1))
done
echo -e "${RED}App did not become healthy within 2 minutes. Please check Docker, logs, and try again.${NC}"
pause_for_debug
exit 1 