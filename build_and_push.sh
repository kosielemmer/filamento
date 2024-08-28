#!/bin/bash

# Set variables
IMAGE_NAME="kosielemmer/filamento"
TAG="latest"
LOG_FILE="docker_build.log"

# Build the Docker image and log the output
echo "Building Docker image..." | tee "$LOG_FILE"
docker build -t "$IMAGE_NAME:$TAG" . 2>&1 | tee -a "$LOG_FILE"

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Docker build completed successfully." | tee -a "$LOG_FILE"
    
    # Push the image to DockerHub
    echo "Pushing image to DockerHub..." | tee -a "$LOG_FILE"
    docker push "$IMAGE_NAME:$TAG" 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Image successfully pushed to DockerHub." | tee -a "$LOG_FILE"
    else
        echo "Failed to push image to DockerHub. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    fi
else
    echo "Docker build failed. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
fi
