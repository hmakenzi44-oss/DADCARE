"""
middleware/jwt_middleware.py — Extracts and validates JWT tokens from httpOnly cookies.
Sets request.global_user and request.active_business on success.
Revoked tokens return None (views enforce auth via decorators, not middleware).
"""
import jwt
from django.conf import settings


class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.global_user = None
        request.active_business = None

        login_token = request.COOKIES.get('dadcare_login_jwt')
        if login_token:
            payload = self._decode(login_token)
            if payload and payload.get('type') == 'login':
                request.global_user = {
                    'id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'full_name': payload.get('full_name'),
                    'jti': payload.get('jti'),
                }

        business_token = request.COOKIES.get('dadcare_business_jwt')
        if business_token:
            payload = self._decode(business_token)
            if payload and payload.get('type') == 'business':
                request.active_business = {
                    'tenant_id': payload.get('tenant_id'),
                    'tenant_name': payload.get('tenant_name'),
                    'schema': payload.get('schema'),
                    'role': payload.get('role'),
                    'permissions': payload.get('permissions', {}),
                    'jti': payload.get('jti'),
                }

        return self.get_response(request)

    def _decode(self, token: str) -> dict | None:
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
