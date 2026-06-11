#!/bin/bash
# Setup SSL certificates for Sangwoo.top
set -e

DOMAIN="sangwoo.top"
EMAIL="${1:-admin@sangwoo.top}"

echo "=== Setting up SSL for $DOMAIN ==="

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily
sudo systemctl stop nginx || sudo docker stop sangwoo-nginx 2>/dev/null || true

# Create ACME challenge directory
sudo mkdir -p /var/www/certbot

# Get certificate
sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email

# Setup auto-renewal
sudo crontab -l | { cat; echo "0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | sudo crontab -

echo "=== SSL setup complete ==="
