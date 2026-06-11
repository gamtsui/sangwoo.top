#!/bin/bash
# Backup Sangwoo.top database and configs
set -e

BACKUP_DIR="/opt/sangwoo.top/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sangwoo_backup_$TIMESTAMP.tar.gz"

mkdir -p $BACKUP_DIR

echo "=== Creating backup: $BACKUP_FILE ==="

# Backup database
tar -czf $BACKUP_FILE \
  -C /opt/sangwoo.top/data sangwoo.db \
  -C /opt/sangwoo.top/backend requirements.txt \
  -C /opt/sangwoo.top/nginx sangwoo.top.conf

# Keep only last 7 backups
ls -t $BACKUP_DIR/*.tar.gz | tail -n +8 | xargs -r rm -f

echo "=== Backup complete ==="
echo "Backup file: $BACKUP_FILE"
