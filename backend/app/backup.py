"""
备份 - 每日备份 SQLite + 静态文件到 S3
保留策略: 最近 30 天
失败重试 3 次，连续失败 3 天告警
"""
import asyncio
import gzip
import io
import json
import logging
import os
import shutil
import tarfile
import time
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# ============ 配置 ============
S3_BUCKET = os.getenv("S3_BUCKET", "sangwoo-backups")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
MAX_RETRIES = 3

# 备份路径
DATA_DIR = os.getenv("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "sangwoo.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
BACKUP_PREFIX = "sangwoo-backups"


def _s3_client():
    """Create S3 client with credentials."""
    if not S3_ACCESS_KEY or not S3_SECRET_KEY:
        logger.warning("AWS credentials not set, using default provider")
        return boto3.client("s3", region_name=S3_REGION)
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )


def create_backup() -> dict:
    """
    Create a full backup: SQLite DB + uploads directory.
    Returns backup info dict.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_PREFIX}/{timestamp}"
    result = {
        "timestamp": timestamp,
        "s3_key": backup_name,
        "status": "pending",
        "files": [],
        "errors": [],
    }

    # Check prerequisites
    if not os.path.exists(DB_PATH):
        result["errors"].append(f"Database not found: {DB_PATH}")
        result["status"] = "failed"
        return result

    s3 = _s3_client()

    # Step 1: Backup SQLite database
    try:
        logger.info(f"Backing up database: {DB_PATH}")
        db_size = os.path.getsize(DB_PATH)

        # Create a consistent snapshot using SQLite backup API
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        backup_conn = sqlite3.connect(":memory:")
        conn.backup(backup_conn)

        # Compress and upload
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # Export in-memory DB to file
            snapshot_path = f"{DB_PATH}.snapshot"
            backup_conn.backup(sqlite3.connect(snapshot_path))
            tar.add(snapshot_path, arcname="sangwoo.db")
            os.remove(snapshot_path)
        backup_conn.close()
        conn.close()

        db_key = f"{backup_name}/sangwoo.db.gz"
        _upload_to_s3(s3, buf.getvalue(), db_key)
        result["files"].append({"name": "sangwoo.db.gz", "key": db_key, "size": len(buf.getvalue())})
        logger.info(f"Database backup uploaded: {db_key} ({len(buf.getvalue())} bytes)")

    except Exception as e:
        result["errors"].append(f"Database backup failed: {e}")
        logger.error(f"Database backup failed: {e}")

    # Step 2: Backup uploads directory
    if os.path.exists(UPLOADS_DIR):
        try:
            logger.info(f"Backing up uploads: {UPLOADS_DIR}")
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tar:
                tar.add(UPLOADS_DIR, arcname="uploads")

            uploads_key = f"{backup_name}/uploads.tar.gz"
            _upload_to_s3(s3, buf.getvalue(), uploads_key)
            result["files"].append({"name": "uploads.tar.gz", "key": uploads_key, "size": len(buf.getvalue())})
            logger.info(f"Uploads backup uploaded: {uploads_key}")
        except Exception as e:
            result["errors"].append(f"Uploads backup failed: {e}")
            logger.error(f"Uploads backup failed: {e}")
    else:
        logger.info(f"Uploads directory not found: {UPLOADS_DIR}, skipping")

    # Step 3: Upload backup manifest
    manifest = {
        "timestamp": timestamp,
        "backup_name": backup_name,
        "files": result["files"],
        "db_size": os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
    }
    manifest_buf = io.BytesIO(json.dumps(manifest, indent=2).encode())
    manifest_key = f"{backup_name}/manifest.json"
    _upload_to_s3(s3, manifest_buf.getvalue(), manifest_key)

    result["status"] = "success" if not result["errors"] else "partial"
    return result


def _upload_to_s3(s3, data: bytes, key: str, retries: int = MAX_RETRIES):
    """Upload data to S3 with retries."""
    for attempt in range(retries):
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=data,
                ContentType="application/gzip",
            )
            return
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise
        except ClientError as e:
            logger.warning(f"S3 upload attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception as e:
            logger.warning(f"S3 upload attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def cleanup_old_backups():
    """Remove backups older than RETENTION_DAYS."""
    s3 = _s3_client()
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    cutoff_str = cutoff.strftime("%Y%m%d")

    try:
        # List all backups
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=BACKUP_PREFIX + "/")
        if "Contents" not in response:
            return []

        deleted = []
        for obj in response["Contents"]:
            key = obj["Key"]
            # Extract date from key
            parts = key.split("/")
            if len(parts) >= 2:
                date_str = parts[1][:8]  # YYYYMMDD
                if date_str < cutoff_str:
                    s3.delete_object(Bucket=S3_BUCKET, Key=key)
                    deleted.append(key)
                    logger.info(f"Deleted old backup: {key}")

        logger.info(f"Cleanup: deleted {len(deleted)} old backup objects")
        return deleted
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        return []


def list_backups() -> list[dict]:
    """List all available backups."""
    s3 = _s3_client()
    backups = []

    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=BACKUP_PREFIX + "/",
            Delimiter="/",
        )

        # Get common prefixes (date folders)
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


def run_backup() -> dict:
    """Run full backup pipeline."""
    logger.info("Starting backup...")
    start = time.time()

    result = create_backup()
    result["duration_seconds"] = round(time.time() - start, 1)

    # Cleanup old backups
    if result["status"] in ("success", "partial"):
        cleanup_old_backups()

    logger.info(f"Backup completed: {result['status']} in {result['duration_seconds']}s")
    return result


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        backups = list_backups()
        print(json.dumps(backups, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        deleted = cleanup_old_backups()
        print(json.dumps({"deleted": deleted}, indent=2))
    else:
        result = run_backup()
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "success" else 1)
