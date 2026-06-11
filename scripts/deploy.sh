#!/bin/bash
# Deploy Sangwoo.top to EC2
set -e

echo "=== Deploying Sangwoo.top ==="

KEY_PATH="C:/Users/GamTsui/sangwoo-key.pem"
if [ ! -f "$KEY_PATH" ]; then
    KEY_PATH="$HOME/sangwoo-key.pem"
fi
if [ ! -f "$KEY_PATH" ]; then
    echo "ERROR: SSH key not found. Set KEY_PATH or place key at expected location."
    exit 1
fi

# Build frontend first
echo "=== Building frontend ==="
cd frontend
npm run build
cd ..

# Copy files to EC2
echo "=== Uploading files ==="

# Frontend dist
scp -r -i "$KEY_PATH" \
  frontend/dist admin@54.226.63.195:/opt/sangwoo/frontend/

# Backend
scp -r -i "$KEY_PATH" \
  backend/ admin@54.226.63.195:/opt/sangwoo/backend/

# Config files
scp -i "$KEY_PATH" \
  docker-compose.yml admin@54.226.63.195:/opt/sangwoo/

scp -r -i "$KEY_PATH" \
  nginx/ admin@54.226.63.195:/opt/sangwoo/nginx/

# Scripts
scp -r -i "$KEY_PATH" \
  scripts/ admin@54.226.63.195:/opt/sangwoo/scripts/

# .env file (if exists)
if [ -f backend/.env ]; then
    scp -i "$KEY_PATH" \
      backend/.env admin@54.226.63.195:/opt/sangwoo/backend/
fi

# SSH and rebuild
echo "=== Deploying on EC2 ==="
ssh -i "$KEY_PATH" -o ConnectTimeout=5 admin@54.226.63.195 << 'EOF'
cd /opt/sangwoo
sudo docker compose down || true
sudo docker compose build
sudo docker compose up -d

# Setup cron jobs
bash /opt/sangwoo/scripts/setup-cron.sh

echo "=== Deployment complete ==="
sudo docker compose ps
EOF
