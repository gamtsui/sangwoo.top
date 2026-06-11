import time
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status

# In-memory store (for production, use Redis)
_login_attempts = defaultdict(list)  # ip -> [timestamps]
_active_sessions = {}  # token -> {username, role, created_at, last_active}

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 1800  # 30 minutes
SESSION_TIMEOUT = 900  # 15 minutes
MAX_SESSIONS_PER_USER = 3

ROLES = {'admin': '管理员', 'readonly': '只读'}


def _is_locked_out(client_ip: str) -> bool:
    now = time.time()
    _login_attempts[client_ip] = [
        t for t in _login_attempts[client_ip] if now - t < LOCKOUT_DURATION
    ]
    return len(_login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS


def _record_failure(client_ip: str) -> None:
    _login_attempts[client_ip].append(time.time())


def check_login_rate_limit(request: Request) -> None:
    """Check if the client IP is locked out due to too many failed login attempts."""
    client_ip = request.client.host if request.client else 'unknown'
    if _is_locked_out(client_ip):
        remaining = int(LOCKOUT_DURATION - (time.time() - max(_login_attempts[client_ip])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f'登录尝试过多，请 {remaining} 秒后重试',
        )


def record_login_failure(request: Request) -> None:
    client_ip = request.client.host if request.client else 'unknown'
    _record_failure(client_ip)


def record_login_success(request: Request) -> None:
    """Clear failed attempts on successful login."""
    client_ip = request.client.host if request.client else 'unknown'
    _login_attempts[client_ip].clear()


def create_session(username: str, role: str = 'admin') -> str:
    """Create a new admin session token."""
    expired = [
        t for t, info in _active_sessions.items()
        if info['username'] == username and _is_session_expired(info)
    ]
    for t in expired:
        del _active_sessions[t]

    user_sessions = [t for t, info in _active_sessions.items() if info['username'] == username]
    if len(user_sessions) >= MAX_SESSIONS_PER_USER:
        oldest = user_sessions[0]
        del _active_sessions[oldest]

    token = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(seconds=SESSION_TIMEOUT)
    _active_sessions[token] = {
        'username': username,
        'role': role,
        'created_at': now,
        'last_active': now,
        'expires': (now + timedelta(seconds=SESSION_TIMEOUT)).timestamp(),
    }
    return token


def _is_session_expired(session_info: dict) -> bool:
    now = datetime.now()
    last_active = session_info.get('last_active') or session_info['created_at']
    return (now - last_active).total_seconds() > SESSION_TIMEOUT


def validate_session(token: Optional[str]) -> dict:
    """Validate session token and return session info. Raises if invalid/expired."""
    if not token:
        raise HTTPException(status_code=401, detail='未登录')
    session_info = _active_sessions.get(token)
    if not session_info:
        raise HTTPException(status_code=401, detail='会话已过期')
    if _is_session_expired(session_info):
        del _active_sessions[token]
        raise HTTPException(status_code=401, detail='会话已超时，请重新登录')
    now = datetime.now()
    session_info['last_active'] = now
    session_info['expires'] = (now + timedelta(seconds=SESSION_TIMEOUT)).timestamp()
    return session_info


def require_role(required_role: str = 'admin'):
    """Dependency factory to check session and role."""
    async def _check(request: Request):
        token = request.cookies.get('admin_token')
        if not token:
            auth = request.headers.get('authorization', '')
            if auth.startswith('Bearer '):
                token = auth[7:]
        session_info = validate_session(token)
        if required_role == 'admin' and session_info['role'] == 'readonly':
            raise HTTPException(status_code=403, detail='权限不足，只读用户无法执行此操作')
        return session_info
    return _check


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions. Call periodically."""
    expired = [t for t, info in _active_sessions.items() if _is_session_expired(info)]
    for t in expired:
        del _active_sessions[t]
    return len(expired)
