#!/bin/bash

# Set the log file path
LOG_FILE="docker_build.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check Docker version
check_docker_version() {
    if ! docker version &>/dev/null; then
        log_message "Error: Unable to get Docker version. Is Docker running?"
        exit 1
    fi
    log_message "Docker is running"
}

# Start logging
log_message "Starting Docker build process"

# Check Docker availability
check_docker_version

# Run the Docker build command and tee the output to both console and log file
if docker build -t kosielemmer/filamento:latest . 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Docker build completed successfully"
else
    log_message "Docker build failed. Please check $LOG_FILE for details"
    exit 1
fi

# Push the Docker image to DockerHub
log_message "Pushing Docker image to DockerHub"
if docker push kosielemmer/filamento:latest 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Docker image pushed to DockerHub successfully"
else
    log_message "Failed to push Docker image to DockerHub. Please check $LOG_FILE for details"
    exit 1
fi

log_message "Build and push process completed"
