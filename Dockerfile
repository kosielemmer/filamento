# Dockerfile for Filament Inventory Application
# Objectives:
# 1. Create a lightweight and secure container for the application
# 2. Ensure all dependencies are properly installed
# 3. Set up the correct environment for running the app
# 4. Optimize for performance and resource usage
# 5. Create a data directory for persistent storage

# Last change: Added data directory for persistent storage (2024-08-28 14:45:00 UTC)

# Use an official Python runtime as a parent image
FROM python:3.9.16-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip and upgrade it
RUN pip install --no-cache-dir --upgrade pip

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Create a non-root user
RUN useradd -m -s /bin/bash appuser

# Create a data directory for persistent storage
RUN mkdir /data && chown -R appuser:appuser /data /app

# Switch to non-root user
USER appuser

# Make port 8090 available to the world outside this container
EXPOSE 8090

# Set the working directory
WORKDIR /app

# Set the Python path to include the current directory
ENV PYTHONPATH=/app

# Run the application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4"]
