#!/usr/bin/env bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

set -e

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
        exit 1
    fi
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker is installed, but the Docker daemon is not running. Please start Docker Desktop or the Docker service and rerun this script.${NC}"
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

echo -e "${CYAN}==> Building the app Docker image locally...${NC}"
if ! docker build -t gemma3n-app:latest .; then
    echo -e "${RED}Docker build failed. Please check your Docker installation and try again.${NC}"
    exit 1
fi

echo -e "${CYAN}==> Building and starting all services...${NC}"
if ! docker-compose up -d --build; then
    echo -e "${RED}docker-compose up failed. Please check your docker-compose.yml and try again.${NC}"
    exit 1
fi

echo -e "${CYAN}==> Waiting for services to become healthy...${NC}"
max_attempts=24
attempt=0
while [[ $attempt -lt $max_attempts ]]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>/dev/null)
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
exit 1 