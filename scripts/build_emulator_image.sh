#!/bin/bash

# Скрипт для сборки Docker образа эмуляции

IMAGE_NAME="virtual-constructor-emulator"
TAG="latest"

echo "Building Docker image ${IMAGE_NAME}:${TAG}..."

docker build -f Dockerfile.emulator -t ${IMAGE_NAME}:${TAG} .

if [ $? -eq 0 ]; then
    echo "Image built successfully!"
    echo "You can now run the server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "Failed to build image!"
    exit 1
fi