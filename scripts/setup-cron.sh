#!/bin/bash
# Setup cron jobs for Sangwoo.top automation
set -e

echo "Setting up cron jobs for Sangwoo.top..."

# Create log directory
mkdir -p /opt/sangwoo/data/logs

# Add cron entries
(crontab -l 2>/dev/null || true) | grep -v "sangwoo" > /tmp/sangwoo.cron
cat /opt/sangwoo/scripts/cron_entries >> /tmp/sangwoo.cron
crontab /tmp/sangwoo.cron
rm /tmp/sangwoo.cron

echo "Cron jobs installed:"
crontab -l

echo "Done."
