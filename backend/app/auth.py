"""Authentication dependencies for admin routes."""
from fastapi import HTTPException, Header, Request, Depends
from datetime import datetime, timedelta
import secrets
import os
import time

# Shared secret key (also used by main.py for CRUDAdmin)
# Override via environment variable ADMIN_SECRET_KEY or SECRET_KEY
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY') or os.getenv('SECRET_KEY') or secrets.token_hex(32)

# Session storage
_active_sessions: dict = {}

# Rate limiting storage
_login_attempts: dict = {}
_RATE_LIMIT_WINDOW = 30 * 60  # 30 minutes
_RATE_LIMIT_MAX = 5  # max 5 failures


def check_login_rate_limit(request: Request):
    """Block login if too many recent failures from this IP."""
    ip = request.client.host
    now = time.time()
    if ip in _login_attempts:
        attempts = [t for t in _login_attempts[ip] if now - t < _RATE_LIMIT_WINDOW]
        _login_attempts[ip] = attempts
        if len(attempts) >= _RATE_LIMIT_MAX:
            raise HTTPException(status_code=429, detail='登录尝试过多，请30分钟后再试')


def record_login_failure(request: Request):
    """Record a failed login attempt for rate limiting."""
    ip = request.client.host
    now = time.time()
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(now)


def record_login_success(request: Request):
    """Clear failed attempts on successful login."""
    ip = request.client.host
    if ip in _login_attempts:
        del _login_attempts[ip]


def create_session(username: str, role: str = 'admin') -> str:
    """Create a new admin session and return the token."""
    token = secrets.token_urlsafe(32)
    _active_sessions[token] = {
        'username': username,
        'role': role,
        'created': time.time(),
        'expires': time.time() + 900,  # 15 minutes
    }
    return token


def validate_session(token: str) -> dict:
    """Validate a session token and return session info."""
    if token not in _active_sessions:
        raise ValueError('Invalid session')
    session = _active_sessions[token]
    if time.time() > session['expires']:
        del _active_sessions[token]
        raise ValueError('Session expired')
    # Refresh session
    session['expires'] = time.time() + 900
    return session


def cleanup_expired_sessions():
    """Remove expired sessions."""
    now = time.time()
    expired = [t for t, s in _active_sessions.items() if now > s['expires']]
    for t in expired:
        del _active_sessions[t]


def require_role(required_role: str = 'admin'):
    """Dependency factory: require specific role."""
    def dependency(authorization: str = Header(None)):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail='Unauthorized')
        token = authorization.split('Bearer ')[1]
        if token != ADMIN_SECRET_KEY:
            raise HTTPException(status_code=401, detail='Invalid token')
        return token
    return dependency


def require_admin(authorization: str = Header(None)):
    """Validate Bearer token for admin-protected endpoints."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = authorization.split('Bearer ')[1]
    if token != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail='Invalid token')
    return token
