from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime
import os
import secrets

from crudadmin import CRUDAdmin

from .database import init_db, get_db, get_session
from .models import (
    Base, Products, News, SiteSettings, AboutCompany, Contact,
    VisitorSubmissions, Analytics, SystemLog, AdminSessions
)
from . import schemas
from .dashboard import router as dashboard_router
from .ai_chat import router as ai_chat_router
from .translate_webhook import router as translate_webhook_router, _trigger_translation
from .analytics import router as analytics_router

# ============ CRUDAdmin Setup ============
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))

admin = CRUDAdmin(
    session=get_session,
    SECRET_KEY=SECRET_KEY,
    initial_admin={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
)

# Add model views
admin.add_view(model=Products, create_schema=schemas.ProductCreate, update_schema=schemas.ProductUpdate)
admin.add_view(model=News, create_schema=schemas.NewsCreate, update_schema=schemas.NewsUpdate)
admin.add_view(model=SiteSettings, create_schema=schemas.SettingCreate, update_schema=schemas.SettingUpdate)
admin.add_view(model=AboutCompany, create_schema=schemas.AboutCreate, update_schema=schemas.AboutUpdate)
admin.add_view(model=Contact, create_schema=schemas.ContactCreate, update_schema=schemas.ContactUpdate)
admin.add_view(model=VisitorSubmissions, create_schema=schemas.SubmissionCreate, update_schema=schemas.SubmissionUpdate, allowed_actions={"view", "delete"})
admin.add_view(model=Analytics, create_schema=schemas.AnalyticsCreate, update_schema=schemas.AnalyticsUpdate, allowed_actions={"view"})
admin.add_view(model=SystemLog, create_schema=schemas.SystemLogCreate, update_schema=schemas.SystemLogUpdate, allowed_actions={"view"})


def require_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = authorization.split('Bearer ')[1]
    if token != SECRET_KEY:
        raise HTTPException(status_code=401, detail='Invalid token')
    return token


# ============ App Setup ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await admin.initialize()
    yield

app = FastAPI(title='Sangwoo.top API', lifespan=lifespan)

# Register dashboard routes BEFORE mounting CRUDAdmin
# (FastAPI matches routes in order, so /admin/dashboard must come first)
app.include_router(dashboard_router)
app.include_router(ai_chat_router)
app.include_router(translate_webhook_router)
app.include_router(analytics_router)

# Mount CRUDAdmin at /admin
app.mount("/admin", admin.app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.middleware("http")
async def admin_middleware(request: Request, call_next):
    """Combined middleware: language cookie + CRUDAdmin i18n injection."""
    path = request.url.path
    response = await call_next(request)

    # Ensure lang cookie is set (only if not already present)
    lang = request.cookies.get('lang')
    if not lang or lang not in ('zh', 'en'):
        response.set_cookie(key='lang', value='zh', max_age=2592000)

    # Inject i18n script into CRUDAdmin HTML pages
    if (path.startswith('/admin') and
        not path.startswith('/admin/dashboard') and
        not path.startswith('/admin/static') and
        'text/html' in response.headers.get('content-type', '')):
        from starlette.responses import StreamingResponse, Response as StarletteResponse
        body = None
        if isinstance(response, StreamingResponse):
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            body = b''.join(chunks)
        elif hasattr(response, 'body') and response.body is not None:
            body = response.body
        if body and isinstance(body, bytes):
            body_str = body.decode('utf-8', errors='replace')
            if '<html' in body_str.lower():
                script = '<script src="/static/crudadmin-i18n.js"></script>'
                body_str = body_str.rstrip().rsplit('</body>', 1)[0] + script + '</body>'
                new_body = body_str.encode('utf-8')
                resp = StarletteResponse(content=new_body, status_code=response.status_code,
                                        media_type='text/html; charset=utf-8')
                for k, v in response.headers.items():
                    if k.lower() not in ('content-length', 'transfer-encoding'):
                        resp.headers[k] = v
                return resp
    return response

# Mount upload directory as static files
from .upload import UPLOAD_DIR as _upload_dir, ensure_dirs as _ensure_dirs
_ensure_dirs()
app.mount("/uploads", StaticFiles(directory=str(_upload_dir)), name="uploads")

# Mount static files for admin interface
from pathlib import Path
static_dir = Path(__file__).parent / 'static'
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 302:
        return RedirectResponse(url='/admin/dashboard/login', status_code=302)
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error'},
    )


# Note: CRUDAdmin provides its own login at /admin
# The require_admin dependency is for the hand-written API endpoints


# ============ Products API ============
@app.get('/api/products')
async def list_products(db=Depends(get_db)):
    return db.query(Products).filter(Products.is_active == True).all()


@app.get('/api/products/{product_id}')
async def get_product(product_id: int, db=Depends(get_db)):
    product = db.query(Products).filter(Products.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


@app.post('/api/products', status_code=201)
async def create_product(data: schemas.ProductCreate, background_tasks: BackgroundTasks, token=Depends(require_admin), db=Depends(get_db)):
    product = Products(**data.model_dump(exclude_unset=True))
    db.add(product)
    db.commit()
    db.refresh(product)
    # Auto-translate Chinese fields to English
    if data.name_zh and not data.name_en:
        background_tasks.add_task(_trigger_translation, 'product', product.id, data.name_zh, 'name_zh', 'name_en')
    if data.description_zh and not data.description_en:
        background_tasks.add_task(_trigger_translation, 'product', product.id, data.description_zh, 'description_zh', 'description_en')
    return product


@app.put('/api/products/{product_id}')
async def update_product(product_id: int, data: schemas.ProductUpdate, token=Depends(require_admin), db=Depends(get_db)):
    db_product = db.query(Products).filter(Products.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail='Product not found')
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete('/api/products/{product_id}', status_code=204)
async def delete_product(product_id: int, token=Depends(require_admin), db=Depends(get_db)):
    db_product = db.query(Products).filter(Products.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail='Product not found')
    db.delete(db_product)
    db.commit()
    return None


# ============ News API ============
@app.get('/api/news')
async def list_news(db=Depends(get_db)):
    return db.query(News).filter(News.status == 'published').all()


@app.get('/api/news/{news_id}')
async def get_news(news_id: int, db=Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail='News not found')
    return news


@app.post('/api/news', status_code=201)
async def create_news(data: schemas.NewsCreate, background_tasks: BackgroundTasks, token=Depends(require_admin), db=Depends(get_db)):
    news = News(**data.model_dump(exclude_unset=True))
    db.add(news)
    db.commit()
    db.refresh(news)
    # Auto-translate Chinese fields to English
    if data.title_zh and not data.title_en:
        background_tasks.add_task(_trigger_translation, 'news', news.id, data.title_zh, 'title_zh', 'title_en')
    if data.content_zh and not data.content_en:
        background_tasks.add_task(_trigger_translation, 'news', news.id, data.content_zh, 'content_zh', 'content_en')
    return news


@app.put('/api/news/{news_id}')
async def update_news(news_id: int, data: schemas.NewsUpdate, token=Depends(require_admin), db=Depends(get_db)):
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail='News not found')
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_news, key, value)
    db.commit()
    db.refresh(db_news)
    return db_news


@app.delete('/api/news/{news_id}', status_code=204)
async def delete_news(news_id: int, token=Depends(require_admin), db=Depends(get_db)):
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail='News not found')
    db.delete(db_news)
    db.commit()
    return None


# ============ Settings API ============
@app.get('/api/settings')
async def get_settings(db=Depends(get_db)):
    settings = db.query(SiteSettings).all()
    return [{"key": s.key, "value": s.value} for s in settings]


@app.get('/api/site-config')
async def get_site_config(db=Depends(get_db)):
    """Return flat site config for frontend: module toggles + key settings."""
    settings = db.query(SiteSettings).all()
    config = {}
    for s in settings:
        config[s.key] = s.value
    # Extract module toggles
    modules = config.get('modules', [])
    if isinstance(modules, list):
        for m in modules:
            if isinstance(m, dict):
                config[m.get('key', '')] = m.get('enabled', True)
    elif isinstance(modules, dict):
        config.update(modules)
    return config


@app.put('/api/settings/{setting_key}')
async def update_setting(setting_key: str, data: schemas.SettingUpdate, token=Depends(require_admin), db=Depends(get_db)):
    db_setting = db.query(SiteSettings).filter(SiteSettings.key == setting_key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail='Setting not found')
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_setting, key, value)
    db.commit()
    db.refresh(db_setting)
    return db_setting


# ============ About API ============
@app.get('/api/about')
async def get_about(db=Depends(get_db)):
    return db.query(AboutCompany).first()


@app.put('/api/about')
async def update_about(data: schemas.AboutUpdate, token=Depends(require_admin), db=Depends(get_db)):
    db_about = db.query(AboutCompany).first()
    if not db_about:
        db_about = AboutCompany(**data.model_dump(exclude_unset=True))
        db.add(db_about)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_about, key, value)
    db.commit()
    db.refresh(db_about)
    return db_about


# ============ Contact API ============
@app.get('/api/contact')
async def get_contact(db=Depends(get_db)):
    return db.query(Contact).first()


@app.put('/api/contact')
async def update_contact(data: schemas.ContactUpdate, token=Depends(require_admin), db=Depends(get_db)):
    db_contact = db.query(Contact).first()
    if not db_contact:
        db_contact = Contact(**data.model_dump(exclude_unset=True))
        db.add(db_contact)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


# ============ Submissions API ============
@app.get('/api/submissions')
async def list_submissions(token=Depends(require_admin), db=Depends(get_db)):
    return db.query(VisitorSubmissions).order_by(VisitorSubmissions.created_at.desc()).all()


@app.post('/api/submissions', status_code=201)
async def create_submission(data: schemas.SubmissionCreate, db=Depends(get_db)):
    submission = VisitorSubmissions(**data.model_dump(exclude_unset=True))
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@app.delete('/api/submissions/{submission_id}', status_code=204)
async def delete_submission(submission_id: int, token=Depends(require_admin), db=Depends(get_db)):
    db_submission = db.query(VisitorSubmissions).filter(VisitorSubmissions.id == submission_id).first()
    if not db_submission:
        raise HTTPException(status_code=404, detail='Submission not found')
    db.delete(db_submission)
    db.commit()
    return None


# ============ Analytics API ============
@app.get('/api/analytics')
async def list_analytics(token=Depends(require_admin), db=Depends(get_db)):
    return db.query(Analytics).order_by(Analytics.date.desc()).limit(1000).all()


@app.post("/api/analytics", status_code=201)
async def create_analytics(data: schemas.AnalyticsCreate, db=Depends(get_db)):
    analytics = Analytics(**data.model_dump(exclude_unset=True))
    db.add(analytics)
    db.commit()
    db.refresh(analytics)
    return analytics


# ============ Automation API ============
@app.post("/api/automation/news")
async def trigger_news_pipeline(token=Depends(require_admin)):
    """Manually trigger the news crawl -> rewrite -> publish pipeline."""
    from .publish import publish_articles
    import asyncio
    try:
        stats = await publish_articles(max_articles=10, days_back=7)
        return {"status": "success", "stats": stats}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/automation/backup")
async def trigger_backup(token=Depends(require_admin)):
    """Manually trigger S3 backup."""
    from .backup import run_backup
    try:
        result = run_backup()
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/automation/health")
async def trigger_health_check(token=Depends(require_admin)):
    """Manually trigger health check."""
    from .health_monitor import run_health_check
    try:
        status = run_health_check()
        return status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/automation/restore/{date_str}")
async def trigger_restore(date_str: str, token=Depends(require_admin)):
    """Restore backup from S3 by date."""
    from .restore import restore_backup
    try:
        result = restore_backup(date_str=date_str)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/automation/backups")
async def list_backups(token=Depends(require_admin)):
    """List available S3 backups."""
    from .backup import list_backups
    try:
        backups = list_backups()
        return {"backups": backups}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============ Health ============
@app.get('/health')
async def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}




