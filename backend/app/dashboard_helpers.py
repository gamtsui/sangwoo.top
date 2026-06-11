import os
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta

from .database import SessionLocal
from .models import SiteSettings

# Default modules
DEFAULT_MODULES = [
    {'key': 'hero_carousel', 'name': 'Hero 轮播', 'description': '首页轮播展示', 'enabled': True},
    {'key': 'product_compare', 'name': '产品对比', 'description': '产品对比功能', 'enabled': True},
    {'key': 'product_finder', 'name': '产品查找器', 'description': '智能产品查找', 'enabled': True},
    {'key': 'honors', 'name': '荣誉资质', 'description': '公司荣誉展示', 'enabled': True},
    {'key': 'ai_chat', 'name': 'AI 客服', 'description': '右下角浮动聊天窗口', 'enabled': True},
    {'key': 'hero_enabled', 'name': '首页 Hero', 'description': '首页顶部展示区域', 'enabled': True},
    {'key': 'products_enabled', 'name': '首页产品展示', 'description': '首页产品展示模块', 'enabled': True},
    {'key': 'news_enabled', 'name': '首页新闻资讯', 'description': '首页新闻模块', 'enabled': True},
    {'key': 'about_enabled', 'name': '首页关于我们', 'description': '首页关于模块', 'enabled': True},
    {'key': 'contact_enabled', 'name': '首页联系我们', 'description': '首页联系模块', 'enabled': True},
]

# Track app start time
APP_START_TIME = time.time()

def _get_health() -> dict:
    """Collect system health metrics."""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_secs = time.time() - APP_START_TIME
    uptime_str = f'{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m'

    return {
        'cpu_percent': cpu,
        'cpu_count': psutil.cpu_count(),
        'mem_percent': mem.percent,
        'mem_used': round(mem.used / 1024**3, 1),
        'mem_total': round(mem.total / 1024**3, 1),
        'disk_percent': disk.percent,
        'disk_used': round(disk.used / 1024**3, 1),
        'disk_total': round(disk.total / 1024**3, 1),
        'uptime': uptime_str,
        'hostname': os.uname().nodename if hasattr(os, 'uname') else os.getenv('HOSTNAME', 'localhost'),
        'platform': os.uname().sysname if hasattr(os, 'uname') else os.name,
        'load_avg': str(os.getloadavg()[:1])[1:-1] if hasattr(os, 'getloadavg') else 'N/A',
    }


def _get_services() -> list:
    """Check service status."""
    services = []
    # Check if current process is healthy
    services.append({
        'name': 'FastAPI Backend',
        'running': True,
        'detail': f'PID {os.getpid()}, uptime {_get_health()["uptime"]}',
    })
    # Check nginx via socket
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('127.0.0.1', 80))
        s.close()
        services.append({'name': 'Nginx', 'running': True, 'detail': 'Port 80 responding'})
    except Exception:
        services.append({'name': 'Nginx', 'running': False, 'detail': 'Port 80 not responding'})
    return services


def _get_storage() -> dict:
    """Calculate upload storage usage."""
    upload_dir = Path('/data/uploads')
    total = 0
    product_size = 0
    if upload_dir.exists():
        for f in upload_dir.rglob('*'):
            if f.is_file():
                size = f.stat().st_size
                total += size
                if 'products' in str(f):
                    product_size += size
    return {
        'total': round(total / 1024 / 1024, 1),
        'products': round(product_size / 1024 / 1024, 1),
        'percent': min(round(total / 1024 / 1024 / 500 * 100, 1), 100),
    }


def _get_modules() -> list:
    """Get module settings from DB or defaults."""
    db = SessionLocal()
    try:
        setting = db.query(SiteSettings).filter(SiteSettings.key == 'modules').first()
        if setting and setting.value:
            return setting.value
        return DEFAULT_MODULES
    finally:
        db.close()


def _save_modules(modules: list) -> None:
    """Save module settings to DB."""
    db = SessionLocal()
    try:
        setting = db.query(SiteSettings).filter(SiteSettings.key == 'modules').first()
        if setting:
            setting.value = modules
        else:
            db.add(SiteSettings(key='modules', value=modules))
        db.commit()
    finally:
        db.close()


def _run_backup() -> dict:
    """Run a manual backup of database and uploads."""
    import tarfile
    backup_dir = Path('/data/backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'sangwoo_backup_{ts}.tar.gz'

    try:
        db_path = Path('/data/sangwoo.db')
        upload_dir = Path('/data/uploads')

        with tarfile.open(str(backup_path), 'w:gz') as tar:
            if db_path.exists():
                tar.add(str(db_path), arcname='sangwoo.db')
            if upload_dir.exists():
                tar.add(str(upload_dir), arcname='uploads')

        size = backup_path.stat().st_size
        return {'status': 'success', 'path': str(backup_path), 'size': f'{round(size/1024, 1)}KB'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _list_backups() -> list:
    """List available backups."""
    backup_dir = Path('/data/backups')
    if not backup_dir.exists():
        return []
    backups = []
    for f in sorted(backup_dir.glob('*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True):
        backups.append({
            'id': f.stem,
            'created_at': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
            'type': 'full',
            'size': f'{round(f.stat().st_size / 1024, 1)}KB',
            'status': 'success',
        })
    return backups[:20]
