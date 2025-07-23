#!/usr/bin/env bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

set -e

echo -e "${CYAN}==> Checking for Docker and Docker Compose...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Please install Docker.${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${CYAN}==> Building the app Docker image locally...${NC}"
docker build -t gemma3n-app:latest .

echo -e "${CYAN}==> Building and starting all services...${NC}"
docker-compose up -d --build

echo -e "${CYAN}==> Waiting for services to become healthy...${NC}"
# Wait for app health
while [[ $(docker inspect --format='{{.State.Health.Status}}' gemma3n-app 2>/dev/null) != "healthy" ]]; do
    echo -e "${YELLOW}Waiting for app to be healthy...${NC}"
    sleep 5
done

echo -e "${GREEN}==> All services are running and healthy!${NC}"
echo -e "${CYAN}==> Access the app at http://localhost:8050${NC}" 