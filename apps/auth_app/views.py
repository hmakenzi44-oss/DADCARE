"""
auth_app/views.py — Registration, login, logout, profile, business selection.
All responses use httpOnly cookies — no tokens in response body.
"""
import json
import hashlib
import secrets
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from apps.auth_app.models import GlobalUser
from apps.tenants.models import Tenant, BusinessMember
from apps.core.jwt_service import (
    create_login_jwt, create_business_jwt,
    set_login_cookie, set_business_cookie, clear_cookies
)
from apps.core.permissions import require_auth, require_business
from apps.core.audit_service import log_action


def hash_password(password: str) -> str:
    """SHA-256 + salt. In production consider bcrypt — swap here only."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hashed = stored_hash.split(':', 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except ValueError:
        return False


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """
    POST /api/auth/register/
    Body: { email, password, full_name, language? }
    Creates GlobalUser, issues login JWT, returns user info.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    language = data.get('language', 'sw')

    # Validation
    if not email or not password or not full_name:
        return JsonResponse(
            {'error': 'email, password, na full_name zinahitajika'},
            status=400
        )
    if len(password) < 8:
        return JsonResponse(
            {'error': 'Nywila lazima iwe na herufi 8 au zaidi'},
            status=400
        )
    if GlobalUser.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Barua pepe hii tayari ipo'}, status=409)

    user = GlobalUser.objects.create(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        language=language,
    )

    log_action(
        action='USER_REGISTERED',
        target_type='global_user',
        target_id=user.id,
        new_value={'email': email, 'full_name': full_name},
        user_id=str(user.id),
        user_name=full_name,
    )

    token = create_login_jwt(user)
    response = JsonResponse({
        'success': True,
        'user': {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'language': user.language,
        }
    }, status=201)
    set_login_cookie(response, token)
    return response


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    POST /api/auth/login/
    Body: { email, password }
    Returns user + their businesses list.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    try:
        user = GlobalUser.objects.get(email=email)
    except GlobalUser.DoesNotExist:
        return JsonResponse({'error': 'Barua pepe au nywila si sahihi'}, status=401)

    if not user.is_active:
        return JsonResponse({'error': 'Akaunti imefungwa'}, status=403)

    if not verify_password(password, user.password_hash):
        return JsonResponse({'error': 'Barua pepe au nywila si sahihi'}, status=401)

    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])

    # Fetch user's businesses
    memberships = BusinessMember.objects.filter(
        global_user=user, is_active=True
    ).select_related('tenant')

    businesses = [
        {
            'id': str(m.tenant.id),
            'name': m.tenant.name,
            'logo_url': m.tenant.logo_url,
            'role': m.role,
            'subscription_status': m.tenant.subscription_status,
            'is_active': m.tenant.is_active,
        }
        for m in memberships
        if m.tenant.is_active
    ]

    log_action(
        action='USER_LOGIN',
        target_type='global_user',
        target_id=user.id,
        user_id=str(user.id),
        user_name=user.full_name,
    )

    token = create_login_jwt(user)
    response = JsonResponse({
        'success': True,
        'user': {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'language': user.language,
            'avatar_url': user.avatar_url,
        },
        'businesses': businesses,
    })
    set_login_cookie(response, token)
    return response


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def select_business(request):
    """
    POST /api/auth/select-business/
    Body: { tenant_id }
    Issues a business JWT for the chosen tenant.
    No logout needed when switching businesses.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    tenant_id = data.get('tenant_id')
    if not tenant_id:
        return JsonResponse({'error': 'tenant_id inahitajika'}, status=400)

    user_id = request.global_user['id']

    try:
        membership = BusinessMember.objects.select_related('tenant').get(
            global_user_id=user_id,
            tenant_id=tenant_id,
            is_active=True,
        )
    except BusinessMember.DoesNotExist:
        return JsonResponse({'error': 'Biashara hii haipatikani'}, status=404)

    tenant = membership.tenant
    if not tenant.is_active:
        return JsonResponse({'error': 'Biashara imefungwa'}, status=403)

    # Check subscription (trial/active only)
    if tenant.subscription_status in ('trial_expired', 'expired', 'suspended'):
        return JsonResponse({
            'error': 'Usajili wa biashara hii umekwisha',
            'subscription_status': tenant.subscription_status,
        }, status=402)

    token = create_business_jwt(
    user=membership.global_user,
        tenant=tenant,
        role=membership.role,
        permissions=membership.custom_permissions,
    )
    
    response = JsonResponse({
        'success': True,
        'business': {
            'id': str(tenant.id),
            'name': tenant.name,
            'role': membership.role,
            'subscription_status': tenant.subscription_status,
        }
    })
    set_business_cookie(response, token)
    return response


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    """POST /api/auth/logout/ — Clears both cookies."""
    response = JsonResponse({'success': True})
    clear_cookies(response)
    return response


@require_http_methods(["GET"])
@require_auth
def profile(request):
    """GET /api/auth/profile/ — Current user info + businesses."""
    user_id = request.global_user['id']

    try:
        user = GlobalUser.objects.get(id=user_id)
    except GlobalUser.DoesNotExist:
        return JsonResponse({'error': 'Mtumiaji hapatikani'}, status=404)

    memberships = BusinessMember.objects.filter(
        global_user=user, is_active=True
    ).select_related('tenant')

    businesses = [
        {
            'id': str(m.tenant.id),
            'name': m.tenant.name,
            'logo_url': m.tenant.logo_url,
            'role': m.role,
            'subscription_status': m.tenant.subscription_status,
        }
        for m in memberships
        if m.tenant.is_active
    ]

    return JsonResponse({
        'user': {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'language': user.language,
            'avatar_url': user.avatar_url,
            'country_code': user.country_code,
        },
        'businesses': businesses,
        'active_business': request.active_business,
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_auth
def update_profile(request):
    """
    PATCH /api/auth/profile/
    Body: { full_name?, language?, country_code?, avatar_url? }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_id = request.global_user['id']
    user = GlobalUser.objects.get(id=user_id)

    allowed_fields = ['full_name', 'language', 'country_code', 'avatar_url']
    updated = {}
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
            updated[field] = data[field]

    if updated:
        user.save(update_fields=list(updated.keys()) + ['updated_at'])
        log_action(
            action='PROFILE_UPDATED',
            target_type='global_user',
            target_id=user.id,
            new_value=updated,
            user_id=str(user.id),
            user_name=user.full_name,
        )

    return JsonResponse({'success': True, 'updated': updated})


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def change_password(request):
    """
    POST /api/auth/change-password/
    Body: { current_password, new_password }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    current = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if len(new_pw) < 8:
        return JsonResponse({'error': 'Nywila mpya lazima iwe na herufi 8+'}, status=400)

    user = GlobalUser.objects.get(id=request.global_user['id'])

    if not verify_password(current, user.password_hash):
        return JsonResponse({'error': 'Nywila ya sasa si sahihi'}, status=401)

    user.password_hash = hash_password(new_pw)
    user.save(update_fields=['password_hash', 'updated_at'])

    log_action(
        action='PASSWORD_CHANGED',
        target_type='global_user',
        target_id=user.id,
        user_id=str(user.id),
        user_name=user.full_name,
    )

    return JsonResponse({'success': True})
