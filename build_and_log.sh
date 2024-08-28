#!/bin/bash

# Set the log file path
LOG_FILE="docker_build.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Start logging
log_message "Starting Docker build process"

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
