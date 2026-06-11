#!/bin/bash
# Setup SSL certificates for Sangwoo.top
set -e

DOMAIN="sangwoo.top"
EMAIL="${1:-admin@sangwoo.top}"

echo "=== Setting up SSL for $DOMAIN ==="

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    sudo yum install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email

# Copy certs to project ssl directory
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ../ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ../ssl/

# Restart nginx
sudo systemctl start nginx

# Setup auto-renewal
sudo crontab -l | { cat; echo "0 3 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

echo "=== SSL setup complete ==="
