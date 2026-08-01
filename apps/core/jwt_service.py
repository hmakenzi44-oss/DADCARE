"""
core/jwt_service.py — JWT creation, validation, and revocation.
Two-layer JWT system:
  1. Login JWT (30 days) — global identity, stored in dadcare_login_jwt cookie
  2. Business JWT (8 hours) — active tenant context, stored in dadcare_business_jwt cookie
"""
import uuid
import jwt
from datetime import datetime, timezone
from django.conf import settings
from django.utils import timezone as dj_timezone


def _now():
    return datetime.now(timezone.utc)


def create_login_jwt(user) -> str:
    """Issue a 30-day login JWT after successful authentication."""
    payload = {
        'type': 'login',
        'jti': str(uuid.uuid4()),
        'user_id': str(user.id),
        'email': user.email,
        'full_name': user.full_name,
        'iat': _now(),
        'exp': _now() + settings.JWT_LOGIN_EXPIRY,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_business_jwt(user, tenant, role: str, permissions: dict) -> str:
    """Issue an 8-hour business JWT after selecting an active business."""
    payload = {
        'type': 'business',
        'jti': str(uuid.uuid4()),
        'user_id': str(user.id),
        'tenant_id': str(tenant.id),
        'tenant_name': tenant.name,
        'schema': tenant.schema_name,
        'role': role,
        'permissions': permissions,
        'iat': _now(),
        'exp': _now() + settings.JWT_BUSINESS_EXPIRY,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload or None."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_revoked(jti: str) -> bool:
    """Check revoked_tokens table. Called on every authenticated request."""
    from apps.auth_app.models import RevokedToken
    return RevokedToken.objects.filter(token_jti=jti).exists()


def revoke_token(jti: str, user_id=None, tenant_id=None, reason: str = '') -> None:
    """Blacklist a JWT immediately — used for employee removal."""
    from apps.auth_app.models import RevokedToken
    RevokedToken.objects.get_or_create(
        token_jti=jti,
        defaults={
            'global_user_id': user_id,
            'tenant_id': tenant_id,
            'reason': reason,
        }
    )


def revoke_all_user_business_tokens(user_id, tenant_id) -> None:
    """
    Called when an employee is removed from a business.
    Since we can't enumerate active JWTs, we store a blanket revocation
    record keyed on user+tenant. The JWT middleware checks this too.
    """
    from apps.auth_app.models import RevokedToken
    # Store a sentinel record — middleware checks (user_id, tenant_id) combos
    RevokedToken.objects.update_or_create(
        token_jti=f"blanket_{user_id}_{tenant_id}",
        defaults={
            'global_user_id': user_id,
            'tenant_id': tenant_id,
            'reason': 'employee_removed',
        }
    )


def set_login_cookie(response, token: str) -> None:
    """Set the login JWT as an httpOnly cookie."""
    response.set_cookie(
        'dadcare_login_jwt',
        token,
        max_age=int(settings.JWT_LOGIN_EXPIRY.total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/',
    )


def set_business_cookie(response, token: str) -> None:
    """Set the business JWT as an httpOnly cookie."""
    response.set_cookie(
        'dadcare_business_jwt',
        token,
        max_age=int(settings.JWT_BUSINESS_EXPIRY.total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/',
    )


def clear_cookies(response) -> None:
    """Clear both JWT cookies on logout."""
    response.delete_cookie('dadcare_login_jwt', path='/')
    response.delete_cookie('dadcare_business_jwt', path='/')
