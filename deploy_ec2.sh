#!/bin/bash
# AutoBlogWriter EC2 deployment script
set -e

# 1. Clone repo if not present
if [ ! -d "AutoBlogWriter" ]; then
  git clone https://github.com/Harooniqbal4879/AutoBlogWriter.git
fi
cd AutoBlogWriter

echo "[INFO] Updating system and installing Docker & Docker Compose..."
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER

echo "[INFO] Copy your .env file to ~/AutoBlogWriter/.env before running this script!"
if [ ! -f ".env" ]; then
  echo "[ERROR] .env file not found. Please upload it before continuing."
  exit 1
fi

echo "[INFO] Building and starting the app with Docker Compose..."
docker compose up --build -d

echo "[SUCCESS] App deployed. Access it at http://<EC2-public-ip>:8501"
