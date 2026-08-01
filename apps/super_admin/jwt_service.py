"""
super_admin/jwt_service.py — JWT for Super Admin panel only.
Uses a separate secret and cookie name from tenant JWTs.
Token type: 'super_admin' — rejected by tenant middleware.
"""
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from django.conf import settings

SA_EXPIRY = timedelta(hours=4)
SA_COOKIE = 'dadcare_sa_jwt'


def _now():
    return datetime.now(timezone.utc)


def create_sa_jwt(admin) -> str:
    payload = {
        'type': 'super_admin',
        'jti': str(uuid.uuid4()),
        'admin_id': str(admin.id),
        'email': admin.email,
        'iat': _now(),
        'exp': _now() + SA_EXPIRY,
    }
    # Use a separate secret for Super Admin — extra isolation
    secret = getattr(settings, 'SA_JWT_SECRET', settings.JWT_SECRET + '_sa')
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def decode_sa_jwt(token: str) -> dict | None:
    try:
        secret = getattr(settings, 'SA_JWT_SECRET', settings.JWT_SECRET + '_sa')
        return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def set_sa_cookie(response, token: str) -> None:
    response.set_cookie(
        SA_COOKIE, token,
        max_age=int(SA_EXPIRY.total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Strict',  # Stricter than tenant cookies
        path='/',
    )


def clear_sa_cookie(response) -> None:
    response.delete_cookie(SA_COOKIE, path='/')
