"""
恢复 - 从 S3 按时间点恢复备份
"""
import io
import json
import logging
import os
import sys
import tarfile
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# ============ 配置 ============
S3_BUCKET = os.getenv("S3_BUCKET", "sangwoo-backups")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
S3_SECRET_KEY=os.getenv("AWS_SECRET_ACCESS_KEY", "")
DATA_DIR = os.getenv("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "sangwoo.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
BACKUP_PREFIX = "sangwoo-backups"


def _s3_client():
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        logger.warning("AWS credentials not set, using default provider")
        return boto3.client("s3", region_name=S3_REGION)
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )


def restore_backup(date_str: str = None, dry_run: bool = False) -> dict:
    """
    Restore backup from S3.
    
    Args:
        date_str: Date string (YYYYMMDD_HHMMSS) or just YYYYMMDD for latest that day.
                  If None, restores the most recent backup.
        dry_run: If True, only show what would be restored.
    
    Returns:
        Result dict with status, files restored, etc.
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "date_requested": date_str,
        "dry_run": dry_run,
        "status": "pending",
        "files_restored": [],
        "errors": [],
    }

    s3 = _s3_client()

    # Find the backup to restore
    backup_key = None
    if date_str:
        backup_key = f"{BACKUP_PREFIX}/{date_str}"
    else:
        # Find most recent backup
        backups = list_available_backups(s3)
        if not backups:
            result["status"] = "failed"
            result["errors"].append("No backups available")
            return result
        backup_key = backups[0]["key"].rstrip("/")

    result["backup_key"] = backup_key

    # Download manifest
    manifest_key = f"{backup_key}/manifest.json"
    try:
        manifest_resp = s3.get_object(Bucket=S3_BUCKET, Key=manifest_key)
        manifest = json.loads(manifest_resp["Body"].read())
        result["manifest"] = manifest
    except ClientError:
        logger.warning(f"No manifest found at {manifest_key}")
        manifest = None

    # Step 1: Restore database
    db_key = f"{backup_key}/sangwoo.db.gz"
    try:
        if dry_run:
            result["files_restored"].append({"name": "sangwoo.db", "action": "would restore"})
        else:
            db_data = _download_from_s3(s3, db_key)
            _restore_database(db_data)
            result["files_restored"].append({"name": "sangwoo.db", "action": "restored"})
            logger.info(f"Database restored from {db_key}")
    except Exception as e:
        result["errors"].append(f"Database restore failed: {e}")
        logger.error(f"Database restore failed: {e}")

    # Step 2: Restore uploads
    uploads_key = f"{backup_key}/uploads.tar.gz"
    try:
        if dry_run:
            result["files_restored"].append({"name": "uploads", "action": "would restore"})
        else:
            uploads_data = _download_from_s3(s3, uploads_key)
            _restore_uploads(uploads_data)
            result["files_restored"].append({"name": "uploads", "action": "restored"})
            logger.info(f"Uploads restored from {uploads_key}")
    except Exception as e:
        result["errors"].append(f"Uploads restore failed: {e}")
        logger.error(f"Uploads restore failed: {e}")

    result["status"] = "success" if not result["errors"] else "partial"
    return result


def _download_from_s3(s3, key: str) -> bytes:
    """Download file from S3."""
    resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return resp["Body"].read()


def _restore_database(data: bytes):
    """Restore SQLite database from gzipped tar."""
    import sqlite3

    # Extract from tar.gz
    buf = io.BytesIO(data)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        db_file = tar.extractfile("sangwoo.db")
        if not db_file:
            raise ValueError("No sangwoo.db in backup archive")
        db_data = db_file.read()

    # Write to temp, then swap
    tmp_path = f"{DB_PATH}.restore.tmp"
    with open(tmp_path, "wb") as f:
        f.write(db_data)

    # Verify integrity
    conn = sqlite3.connect(tmp_path)
    conn.execute("PRAGMA integrity_check")
    conn.close()

    # Backup current DB before overwriting
    if os.path.exists(DB_PATH):
        backup_current = f"{DB_PATH}.pre_restore_{int(time.time())}"
        os.rename(DB_PATH, backup_current)
        logger.info(f"Current DB backed up to {backup_current}")

    # Move new DB into place
    os.rename(tmp_path, DB_PATH)
    logger.info(f"Database restored to {DB_PATH}")


def _restore_uploads(data: bytes):
    """Restore uploads directory from gzipped tar."""
    buf = io.BytesIO(data)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        tar.extractall(path=DATA_DIR)
    logger.info(f"Uploads restored to {UPLOADS_DIR}")


def list_available_backups(s3=None) -> list[dict]:
    """List all available backups sorted by date (newest first)."""
    if s3 is None:
        s3 = _s3_client()

    backups = []
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=BACKUP_PREFIX + "/",
            Delimiter="/",
        )

        for prefix in response.get("CommonPrefixes", []):
            date_str = prefix["Prefix"].split("/")[-2]
            backups.append({
                "date": date_str,
                "key": prefix["Prefix"],
            })

        backups.sort(key=lambda x: x["date"], reverse=True)
    except Exception as e:
        logger.error(f"List backups failed: {e}")

    return backups


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    parser = argparse.ArgumentParser(description="Restore Sangwoo backup from S3")
    parser.add_argument("date", nargs="?", default=None, help="Backup date (YYYYMMDD or YYYYMMDD_HHMMSS)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be restored")
    parser.add_argument("--list", action="store_true", help="List available backups")
    args = parser.parse_args()

    if args.list:
        s3 = _s3_client()
        backups = list_available_backups(s3)
        print(json.dumps(backups, indent=2))
    else:
        result = restore_backup(date_str=args.date, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["status"] == "success" else 1)
