"""
super_admin/middleware.py — Validates Super Admin JWT on every request.
Only active for control.dadcare.app domain.
Sets request.super_admin on success.
"""
from apps.super_admin.jwt_service import decode_sa_jwt, SA_COOKIE
from apps.super_admin.models import SuperAdminSession


class SuperAdminMiddleware:
    """
    Injected into the request pipeline only for the SA subdomain.
    Checks: valid JWT type, session not revoked, admin still active.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.super_admin = None
        request.is_super_admin = False

        token = request.COOKIES.get(SA_COOKIE)
        if token:
            payload = decode_sa_jwt(token)
            if payload and payload.get('type') == 'super_admin':
                jti = payload.get('jti')
                try:
                    session = SuperAdminSession.objects.select_related('admin').get(
                        token_jti=jti, is_revoked=False
                    )
                    if session.admin.is_active:
                        request.super_admin = {
                            'id': str(session.admin.id),
                            'email': session.admin.email,
                            'full_name': session.admin.full_name,
                            'jti': jti,
                        }
                        request.is_super_admin = True
                except SuperAdminSession.DoesNotExist:
                    pass

        return self.get_response(request)


import functools
from django.http import JsonResponse


def require_super_admin(view_func):
    """Decorator: blocks non-Super-Admin requests with 403."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.is_super_admin:
            return JsonResponse({'error': 'Super Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
