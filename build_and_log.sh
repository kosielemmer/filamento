#!/bin/bash

# Set the log file path
LOG_FILE="docker_build.log"

# Run the Docker build command and tee the output to both console and log file
docker build -t filament-inventory-app:latest . | tee "$LOG_FILE"

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Docker build completed successfully. Log saved to $LOG_FILE"
else
    echo "Docker build failed. Please check $LOG_FILE for details."
fi
