"""Authentication dependencies for admin routes."""
from fastapi import HTTPException, Header
import secrets

# Shared secret key (also used by main.py for CRUDAdmin)
# Override via environment variable ADMIN_SECRET_KEY or SECRET_KEY
import os
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY') or os.getenv('SECRET_KEY') or secrets.token_hex(32)


def require_admin(authorization: str = Header(None)):
    """Validate Bearer token for admin-protected endpoints."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = authorization.split('Bearer ')[1]
    if token != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail='Invalid token')
    return token
