#!/bin/bash

# Set the log file path
LOG_FILE="docker_build.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check Docker version
check_docker_version() {
    docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_message "Error: Unable to get Docker version. Is Docker running?"
        exit 1
    fi
    log_message "Docker version: $docker_version"
}

# Function to check Docker Compose version
check_docker_compose_version() {
    compose_version=$(docker-compose version --short 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_message "Error: Unable to get Docker Compose version. Is it installed?"
        exit 1
    fi
    log_message "Docker Compose version: $compose_version"
}

# Start logging
log_message "Starting Docker build process"

# Check Docker and Docker Compose versions
check_docker_version
check_docker_compose_version

# Run the Docker build command and tee the output to both console and log file
if docker build -t filament-inventory-app:latest . 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Docker build completed successfully"
else
    log_message "Docker build failed. Please check $LOG_FILE for details"
    exit 1
fi

# Run Docker Compose
log_message "Starting Docker Compose"
if docker-compose up -d 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Docker Compose started successfully"
else
    log_message "Docker Compose failed to start. Please check $LOG_FILE for details"
    exit 1
fi

log_message "Build and deployment process completed"
