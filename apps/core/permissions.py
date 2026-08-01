"""
core/permissions.py — DRF-style permission decorators for view functions.
Used as @require_auth, @require_business, @require_permission('can_void_sales').
"""
import functools
from django.http import JsonResponse
from apps.core.jwt_service import is_token_revoked


def require_auth(view_func):
    """Require a valid login JWT. Sets request.global_user."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, 'global_user', None)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Check revocation
        jti = user.get('jti')
        if jti and is_token_revoked(jti):
            return JsonResponse({'error': 'Session revoked'}, status=401)

        return view_func(request, *args, **kwargs)
    return wrapper


def require_business(view_func):
    """Require both login JWT and an active business JWT."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, 'global_user', None)
        business = getattr(request, 'active_business', None)

        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not business:
            return JsonResponse({'error': 'No active business selected'}, status=403)

        # Check blanket revocation (employee removed)
        user_id = user.get('id')
        tenant_id = business.get('tenant_id')
        sentinel = f"blanket_{user_id}_{tenant_id}"
        if is_token_revoked(sentinel):
            return JsonResponse({'error': 'Access to this business has been revoked'}, status=403)

        # Check business JWT JTI
        jti = business.get('jti')
        if jti and is_token_revoked(jti):
            return JsonResponse({'error': 'Business session revoked'}, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(*roles):
    """Require specific role(s) in the active business."""
    def decorator(view_func):
        @functools.wraps(view_func)
        @require_business
        def wrapper(request, *args, **kwargs):
            role = request.active_business.get('role')
            if role not in roles:
                return JsonResponse(
                    {'error': f'Role required: {", ".join(roles)}'},
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission_key: str):
    """Require a custom permission in the active business JWT."""
    def decorator(view_func):
        @functools.wraps(view_func)
        @require_business
        def wrapper(request, *args, **kwargs):
            business = request.active_business
            role = business.get('role')
            permissions = business.get('permissions', {})

            # Owners bypass all permission checks
            if role == 'owner':
                return view_func(request, *args, **kwargs)

            if not permissions.get(permission_key, False):
                return JsonResponse(
                    {'error': f'Permission denied: {permission_key}'},
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_owner(view_func):
    """Shortcut: owner only."""
    return require_role('owner')(view_func)


def require_manager_or_above(view_func):
    """Shortcut: owner or manager."""
    return require_role('owner', 'manager')(view_func)
