import os
import psutil
import time
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import jinja2
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from sqlalchemy import func

from .database import get_db, SessionLocal
from .models import Products, News, VisitorSubmissions, Analytics, SystemLog, SiteSettings
from .upload import upload_product_images, ensure_dirs, UPLOAD_DIR
from .dashboard_helpers import (
    _get_health, _get_services, _get_storage,
    _get_modules, _save_modules,
    _run_backup, _list_backups,
)
from .auth import (
    check_login_rate_limit, record_login_failure, record_login_success,
    create_session, validate_session, cleanup_expired_sessions, require_role,
    _active_sessions,
)
from .i18n import get_locale, t as _t

router = APIRouter()

TEMPLATE_DIR = Path(__file__).parent / 'templates'
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(['html']),
)

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')


def _make_t(locale: str):
    return lambda key, **kw: _t(key, locale=locale, **kw)


def _render(template_name: str, request: Request, **ctx) -> HTMLResponse:
    locale = get_locale(request)
    ctx.setdefault('locale', locale)
    ctx['_'] = _make_t(locale)
    ctx['redirect_uri'] = str(request.url)
    tmpl = env.get_template(template_name)
    html = tmpl.render(**ctx)
    return HTMLResponse(content=html)


def require_dashboard(request: Request):
    """Check dashboard session. Raise if not authenticated."""
    from fastapi import HTTPException
    token = request.cookies.get('admin_token')
    if not token:
        raise HTTPException(status_code=302, detail='未登录')
    try:
        session_info = validate_session(token)
        return session_info
    except Exception:
        raise HTTPException(status_code=302, detail='会话过期')


@router.get('/admin/dashboard/login', response_class=HTMLResponse)
async def dashboard_login(request: Request):
    locale = get_locale(request)
    tmpl = env.get_template('dashboard/login.html')
    html = tmpl.render(locale=locale, _=_make_t(locale))
    return HTMLResponse(content=html)


@router.post('/admin/dashboard/login', response_class=HTMLResponse)
async def dashboard_login_post(request: Request):
    check_login_rate_limit(request)
    form = await request.form()
    username = form.get('username', '')
    password = form.get('password', '')
    locale = get_locale(request)
    _ = _make_t(locale)
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        record_login_failure(request)
        tmpl = env.get_template('dashboard/login.html')
        html = tmpl.render(locale=locale, _=_,
                           username=username, error=_('login_failed'))
        return HTMLResponse(content=html)
    record_login_success(request)
    token = create_session(username, 'admin')
    response = RedirectResponse(url='/admin/dashboard', status_code=302)
    response.set_cookie(key='admin_token', value=token, httponly=True, max_age=900)
    return response


@router.get('/admin/dashboard/lang', response_class=RedirectResponse)
async def switch_lang(request: Request, lang: str = Query('zh')):
    if lang not in ('zh', 'en'):
        lang = 'zh'
    response = RedirectResponse(url=request.query_params.get('redirect', '/admin/dashboard'), status_code=302)
    response.set_cookie(key='lang', value=lang, max_age=2592000)
    return response


@router.get('/admin/dashboard', response_class=HTMLResponse)
async def dashboard_overview(request: Request, session=Depends(require_dashboard), db=Depends(get_db)):
    product_count = db.query(Products).count()
    news_count = db.query(News).filter(News.status == 'published').count()
    submission_count = db.query(VisitorSubmissions).count()
    today = datetime.now().date()
    today_views = db.query(Analytics).filter(Analytics.date >= today).count()
    recent_logs = db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(10).all()
    health = _get_health()
    return _render('dashboard/overview.html', request, active='overview',
                   username=session.get('username', 'admin'),
                   product_count=product_count, news_count=news_count,
                   submission_count=submission_count, today_views=today_views,
                   recent_logs=recent_logs, health=health)


@router.get('/admin/dashboard/analytics', response_class=HTMLResponse)
async def dashboard_analytics(request: Request, session=Depends(require_dashboard), db=Depends(get_db)):
    days = 30
    labels, pv_data, uv_data = [], [], []
    for i in range(days, 0, -1):
        d = (datetime.now() - timedelta(days=i)).date()
        next_d = (datetime.now() - timedelta(days=i - 1)).date()
        labels.append(d.strftime('%m/%d'))
        pv = db.query(Analytics).filter(Analytics.date >= d, Analytics.date < next_d).count()
        uv = db.query(func.distinct(Analytics.cookie_id)).filter(Analytics.date >= d, Analytics.date < next_d).scalar() or 0
        pv_data.append(pv)
        uv_data.append(uv)
    top_pages = db.query(Analytics.page, func.count(Analytics.id).label('count')) \
        .group_by(Analytics.page).order_by(func.count(Analytics.id).desc()).limit(10).all()
    top_sources = db.query(Analytics.source, func.count(Analytics.id).label('count')) \
        .group_by(Analytics.source).order_by(func.count(Analytics.id).desc()).limit(10).all()
    return _render('dashboard/analytics.html', request, active='analytics',
                   username=session.get('username', 'admin'),
                   chart_labels=labels, chart_pv=pv_data, chart_uv=uv_data,
                   top_pages=top_pages, top_sources=top_sources)


@router.get('/admin/dashboard/modules', response_class=HTMLResponse)
async def dashboard_modules(request: Request, session=Depends(require_dashboard)):
    modules = _get_modules()
    return _render('dashboard/modules.html', request, active='modules',
                   username=session.get('username', 'admin'), modules=modules)


@router.post('/api/admin/modules')
async def save_modules(request: Request, session=Depends(require_role('admin'))):
    form = await request.form()
    modules = _get_modules()
    for m in modules:
        m['enabled'] = form.get(m['key']) == 'true'
    _save_modules(modules)
    locale = get_locale(request)
    return {'status': 'success', 'message': _t('saved', locale=locale)}


@router.get('/admin/dashboard/health', response_class=HTMLResponse)
async def dashboard_health(request: Request, session=Depends(require_dashboard), db=Depends(get_db)):
    health = _get_health()
    services = _get_services()
    recent_errors = db.query(SystemLog).filter(
        SystemLog.level.in_(['error', 'warning'])
    ).order_by(SystemLog.created_at.desc()).limit(20).all()
    return _render('dashboard/health.html', request, active='health',
                   username=session.get('username', 'admin'), health=health, services=services,
                   recent_errors=recent_errors)


@router.get('/admin/dashboard/backup', response_class=HTMLResponse)
async def dashboard_backup(request: Request, session=Depends(require_dashboard)):
    backups = _list_backups()
    return _render('dashboard/backup.html', request, active='backup',
                   username=session.get('username', 'admin'), backups=backups, auto_backup=False)


@router.post('/api/admin/backup/run')
async def run_full_backup(request: Request, session=Depends(require_role('admin'))):
    result = _run_backup()
    return result


@router.post('/api/admin/backup/db')
async def run_db_backup(request: Request, session=Depends(require_role('admin'))):
    import tarfile
    backup_dir = Path('/data/backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'sangwoo_db_{ts}.tar.gz'
    try:
        db_path = Path('/data/sangwoo.db')
        with tarfile.open(str(backup_path), 'w:gz') as tar:
            if db_path.exists():
                tar.add(str(db_path), arcname='sangwoo.db')
        return {'status': 'success', 'message': f'数据库备份完成: {backup_path.name}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@router.get('/admin/dashboard/uploads', response_class=HTMLResponse)
async def dashboard_uploads(request: Request, session=Depends(require_dashboard)):
    storage = _get_storage()
    ensure_dirs()
    return _render('dashboard/uploads.html', request, active='uploads',
                   username=session.get('username', 'admin'), storage=storage)


@router.post('/api/admin/upload')
async def upload_files(request: Request, session=Depends(require_role('admin')),
    product_slug: str = Form(...),
    files: list[UploadFile] = File(...),
    db=Depends(get_db)):
    ensure_dirs()
    results = await upload_product_images(files, product_slug)
    product = db.query(Products).filter(Products.slug == product_slug).first()
    if product:
        existing = product.images or []
        existing.extend(results)
        product.images = existing
        db.commit()
    return {'status': 'success', 'count': len(results), 'paths': results}


@router.get('/api/admin/session/check')
async def check_session(request: Request):
    """HTMX session check endpoint for background polling."""
    token = request.cookies.get('admin_token')
    if token and validate_session(token):
        sess = validate_session(token)
        remaining = int(sess['expires'] - time.time())
        if remaining <= 60:
            _ = _make_t(get_locale(request))
            return JSONResponse(content={'status': 'expiring', 'remaining': remaining,
                                         'message': _('session_expiring', default='会话即将过期')})
        return JSONResponse(content={'status': 'ok', 'remaining': remaining})
    return JSONResponse(content={'status': 'expired', 'remaining': 0})


@router.get('/api/admin/health')
async def api_health():
    return {**_get_health(), 'services': _get_services()}


@router.get('/api/admin/modules')
async def get_modules_api():
    return _get_modules()


@router.post('/api/admin/logout')
async def admin_logout(request: Request):
    token = request.cookies.get('admin_token')
    if token and token in _active_sessions:
        del _active_sessions[token]
    response = JSONResponse(content={'status': 'logged out'})
    response.delete_cookie('admin_token')
    response.headers['HX-Redirect'] = '/admin/dashboard/login'
    return response
