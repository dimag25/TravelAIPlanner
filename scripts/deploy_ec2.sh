#!/bin/bash

# EC2 Deployment Script
echo "Starting deployment to EC2..."

# Load environment variables
set -a
source .env
set +a

# Update instance and install dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Pull latest code and rebuild
git pull origin main

# Build and start containers
sudo docker-compose build
sudo docker-compose up -d

echo "Deployment completed successfully!"
