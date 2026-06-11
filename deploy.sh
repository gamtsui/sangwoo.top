#!/bin/bash
set -e

EC2_USER="admin"
EC2_HOST="54.226.63.195"
EC2_DIR="/home/admin/sangwoo.top"
KEY_FILE="/c/Users/GamTsui/sangwoo-key.pem"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Sync backend
echo "=== Syncing backend to EC2 ==="
scp -i "$KEY_FILE" -r "$PROJECT_DIR/backend" "$EC_USER@$EC2_HOST:$EC2_DIR/"

# Sync frontend (without node_modules/dist)
echo "=== Syncing frontend to EC2 ==="
(cd "$PROJECT_DIR/frontend" && tar czf - --exclude='node_modules' --exclude='dist' .) | ssh -i "$KEY_FILE" "$EC_USER@$EC2_HOST" "cd $EC2_DIR/frontend && tar xzf -"

# Sync nginx + docker-compose
echo "=== Syncing configs ==="
scp -i "$KEY_FILE" -r "$PROJECT_DIR/nginx" "$EC_USER@$EC2_HOST:$EC2_DIR/"
scp -i "$KEY_FILE" "$PROJECT_DIR/docker-compose.yml" "$EC_USER@$EC2_HOST:$EC2_DIR/"
scp -i "$KEY_FILE" -r "$PROJECT_DIR/scripts" "$EC_USER@$EC2_HOST:$EC2_DIR/"

# Build + deploy on EC2
echo "=== Building and deploying on EC2 ==="
ssh -i "$KEY_FILE" "$EC_USER@$EC2_HOST" << 'ENDSSH'
cd /home/admin/sangwoo.top

# Create data directory
mkdir -p data

# Start backend first so frontend build can fetch data
docker compose up -d backend
sleep 3

# Build frontend (static generation with live API)
cd /home/admin/sangwoo.top/frontend
npm ci
BUILD_API="http://localhost:8000" npm run build

# Restart full stack
cd /home/admin/sangwoo.top
docker compose down
docker compose build
docker compose up -d
ENDSSH

echo "=== Deploy complete ==="
