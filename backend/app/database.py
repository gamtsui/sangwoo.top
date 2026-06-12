from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .models import Base
import os

# Docker volume mounts ../data to /data; fall back to relative path for local dev
DATA_DIR = '/data' if os.path.isdir('/data') else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'sangwoo.db')

DATABASE_URL = f'sqlite:///{DB_PATH}'
ASYNC_DATABASE_URL = f'sqlite+aiosqlite:///{DB_PATH}'

# Sync engine — used by existing API endpoints
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine — used by CRUDAdmin
async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args={'check_same_thread': False})


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    _seed_default_modules()


def _migrate_db():
    """Apply incremental migrations to existing tables."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # Add `source` column to analytics if missing
        result = db.execute(text("PRAGMA table_info(analytics)"))
        columns = {row[1] for row in result.fetchall()}
        if 'source' not in columns:
            db.execute(text("ALTER TABLE analytics ADD COLUMN source TEXT DEFAULT 'direct'"))
            db.commit()

        # Add `price` column to products if missing
        result = db.execute(text("PRAGMA table_info(products)"))
        columns = {row[1] for row in result.fetchall()}
        if 'price' not in columns:
            db.execute(text("ALTER TABLE products ADD COLUMN price REAL DEFAULT NULL"))
            db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Migration warning: {e}")
    finally:
        db.close()


def _seed_default_modules():
    """Seed default module toggles if not present."""
    from .models import SiteSettings
    from .dashboard_helpers import DEFAULT_MODULES

    db = SessionLocal()
    try:
        existing = db.query(SiteSettings).filter(SiteSettings.key == 'modules').first()
        if not existing:
            # Check if any of the new default keys exist in modules
            db.add(SiteSettings(key='modules', value=DEFAULT_MODULES))
            db.commit()
    finally:
        db.close()


def get_db():
    """Sync session generator for API endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_session():
    """Async session generator for CRUDAdmin."""
    async with AsyncSession(async_engine) as session:
        yield session
