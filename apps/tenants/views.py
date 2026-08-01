"""
tenants/views.py — Business registration, invite codes, member management.
"""
import json
import secrets
import string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta

from apps.tenants.models import (
    Tenant, BusinessMember, MiniApp, InviteCode, SubscriptionPayment
)
from apps.auth_app.models import GlobalUser, RevokedToken
from apps.core.permissions import require_auth, require_business, require_owner, require_manager_or_above
from apps.core.audit_service import log_action
from apps.core.jwt_service import revoke_all_user_business_tokens
from apps.tenants.schema_service import provision_tenant_schema


def _generate_invite_code(length=10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _slugify(name: str) -> str:
    import re
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug[:50]


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_business(request):
    """
    POST /api/tenants/create/
    Body: { name, mini_app_slug, city?, country_code?, phone?, whatsapp?, description? }
    Creates tenant + provisions PostgreSQL schema + assigns owner role.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    mini_app_slug = data.get('mini_app_slug', 'shop')

    if not name:
        return JsonResponse({'error': 'Jina la biashara linahitajika'}, status=400)

    try:
        mini_app = MiniApp.objects.get(slug=mini_app_slug, is_active=True)
    except MiniApp.DoesNotExist:
        return JsonResponse({'error': 'Mini-app haipatikani'}, status=404)

    # Generate unique slug
    base_slug = _slugify(name)
    slug = base_slug
    counter = 1
    while Tenant.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    user_id = request.global_user['id']
    user = GlobalUser.objects.get(id=user_id)

    tenant = Tenant.objects.create(
        name=name,
        slug=slug,
        mini_app=mini_app,
        city=data.get('city', ''),
        country_code=data.get('country_code', ''),
        phone=data.get('phone', ''),
        whatsapp=data.get('whatsapp', ''),
        description=data.get('description', ''),
        subscription_status='trial',
    )

    # Create owner membership
    BusinessMember.objects.create(
        global_user=user,
        tenant=tenant,
        role='owner',
        invited_by=user,
    )

    # Provision PostgreSQL schema
    try:
        provision_tenant_schema(str(tenant.id))
    except Exception as e:
        # Roll back tenant creation if schema fails
        tenant.delete()
        return JsonResponse(
            {'error': f'Hitilafu ya mfumo wa hifadhidata: {str(e)}'},
            status=500
        )

    log_action(
        action='BUSINESS_CREATED',
        target_type='tenant',
        target_id=tenant.id,
        new_value={'name': name, 'slug': slug, 'mini_app': mini_app_slug},
        user_id=str(user.id),
        user_name=user.full_name,
        tenant_id=str(tenant.id),
    )

    return JsonResponse({
        'success': True,
        'business': {
            'id': str(tenant.id),
            'name': tenant.name,
            'slug': tenant.slug,
            'subscription_status': tenant.subscription_status,
            'trial_expires_at': tenant.trial_expires_at.isoformat(),
        }
    }, status=201)


@require_http_methods(["GET"])
@require_business
def business_detail(request):
    """GET /api/tenants/me/ — Active business info."""
    tenant_id = request.active_business['tenant_id']
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Biashara haipatikani'}, status=404)

    return JsonResponse({
        'id': str(tenant.id),
        'name': tenant.name,
        'slug': tenant.slug,
        'logo_url': tenant.logo_url,
        'city': tenant.city,
        'country_code': tenant.country_code,
        'phone': tenant.phone,
        'whatsapp': tenant.whatsapp,
        'description': tenant.description,
        'subscription_status': tenant.subscription_status,
        'trial_expires_at': tenant.trial_expires_at.isoformat() if tenant.trial_expires_at else None,
        'subscription_expires_at': tenant.subscription_expires_at.isoformat() if tenant.subscription_expires_at else None,
        'role': request.active_business['role'],
        'permissions': request.active_business['permissions'],
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_owner
def update_business(request):
    """PATCH /api/tenants/me/update/ — Update business details (owner only)."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    tenant_id = request.active_business['tenant_id']
    tenant = Tenant.objects.get(id=tenant_id)

    allowed = ['name', 'city', 'country_code', 'phone', 'whatsapp', 'description', 'logo_url']
    old_value = {f: getattr(tenant, f) for f in allowed}
    updated = {}

    for field in allowed:
        if field in data:
            setattr(tenant, field, data[field])
            updated[field] = data[field]

    if updated:
        tenant.save(update_fields=list(updated.keys()))
        log_action(
            action='BUSINESS_UPDATED',
            target_type='tenant',
            target_id=tenant.id,
            old_value=old_value,
            new_value=updated,
            user_id=request.global_user['id'],
            user_name=request.global_user['full_name'],
            tenant_id=str(tenant.id),
        )

    return JsonResponse({'success': True, 'updated': updated})


@require_http_methods(["GET"])
@require_business
def list_members(request):
    """GET /api/tenants/members/ — All members of active business."""
    tenant_id = request.active_business['tenant_id']
    members = BusinessMember.objects.filter(
        tenant_id=tenant_id
    ).select_related('global_user')

    return JsonResponse({
        'members': [
            {
                'id': str(m.id),
                'user_id': str(m.global_user.id),
                'name': m.global_user.full_name,
                'email': m.global_user.email,
                'role': m.role,
                'permissions': m.custom_permissions,
                'is_active': m.is_active,
                'joined_at': m.joined_at.isoformat(),
            }
            for m in members
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_owner
def create_invite(request):
    """
    POST /api/tenants/invite/
    Body: { role, custom_permissions?, max_uses? }
    Returns invite code valid for 7 days.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    role = data.get('role', 'staff')
    valid_roles = ['manager', 'cashier', 'staff', 'viewer']
    if role not in valid_roles:
        return JsonResponse({'error': f'Role lazima iwe: {", ".join(valid_roles)}'}, status=400)

    tenant_id = request.active_business['tenant_id']
    user = GlobalUser.objects.get(id=request.global_user['id'])

    code = _generate_invite_code()
    while InviteCode.objects.filter(code=code).exists():
        code = _generate_invite_code()

    invite = InviteCode.objects.create(
        tenant_id=tenant_id,
        created_by=user,
        role=role,
        custom_permissions=data.get('custom_permissions', {}),
        code=code,
        max_uses=data.get('max_uses', 1),
        expires_at=timezone.now() + timedelta(days=7),
    )

    log_action(
        action='INVITE_CREATED',
        target_type='invite_code',
        target_id=invite.id,
        new_value={'role': role, 'code': code},
        user_id=str(user.id),
        user_name=user.full_name,
        tenant_id=str(tenant_id),
    )

    return JsonResponse({
        'success': True,
        'invite': {
            'code': code,
            'role': role,
            'expires_at': invite.expires_at.isoformat(),
            'max_uses': invite.max_uses,
        }
    }, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def join_business(request):
    """
    POST /api/tenants/join/
    Body: { code }
    Validates invite code and creates BusinessMember.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    code = data.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'error': 'Nambari ya mwaliko inahitajika'}, status=400)

    try:
        invite = InviteCode.objects.select_related('tenant').get(code=code)
    except InviteCode.DoesNotExist:
        return JsonResponse({'error': 'Nambari ya mwaliko si sahihi'}, status=404)

    if not invite.is_valid:
        return JsonResponse({'error': 'Mwaliko huu umekwisha muda au umetumiwa'}, status=410)

    user = GlobalUser.objects.get(id=request.global_user['id'])

    # Check if already a member
    if BusinessMember.objects.filter(global_user=user, tenant=invite.tenant).exists():
        return JsonResponse({'error': 'Tayari wewe ni mwanachama wa biashara hii'}, status=409)

    member = BusinessMember.objects.create(
        global_user=user,
        tenant=invite.tenant,
        role=invite.role,
        custom_permissions=invite.custom_permissions,
        invited_by=invite.created_by,
    )

    # Increment usage count
    invite.uses += 1
    invite.save(update_fields=['uses'])

    log_action(
        action='MEMBER_JOINED',
        target_type='business_member',
        target_id=member.id,
        new_value={'role': invite.role, 'via_invite': code},
        user_id=str(user.id),
        user_name=user.full_name,
        tenant_id=str(invite.tenant.id),
    )

    return JsonResponse({
        'success': True,
        'business': {
            'id': str(invite.tenant.id),
            'name': invite.tenant.name,
            'role': invite.role,
        }
    })


@csrf_exempt
@require_http_methods(["DELETE"])
@require_owner
def remove_member(request, member_id):
    """
    DELETE /api/tenants/members/<member_id>/remove/
    Deactivates membership and immediately revokes all their business tokens.
    """
    tenant_id = request.active_business['tenant_id']

    try:
        member = BusinessMember.objects.select_related('global_user').get(
            id=member_id, tenant_id=tenant_id
        )
    except BusinessMember.DoesNotExist:
        return JsonResponse({'error': 'Mwanachama hapatikani'}, status=404)

    if member.role == 'owner':
        return JsonResponse({'error': 'Mwenye biashara hawezi kuondolewa'}, status=403)

    user_id = str(member.global_user.id)
    member.is_active = False
    member.save(update_fields=['is_active'])

    # Immediately revoke access — no waiting for token expiry
    revoke_all_user_business_tokens(user_id, tenant_id)

    log_action(
        action='MEMBER_REMOVED',
        target_type='business_member',
        target_id=member.id,
        old_value={'role': member.role, 'user': member.global_user.email},
        user_id=request.global_user['id'],
        user_name=request.global_user['full_name'],
        tenant_id=str(tenant_id),
    )

    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["PATCH"])
@require_owner
def update_member_permissions(request, member_id):
    """
    PATCH /api/tenants/members/<member_id>/permissions/
    Body: { custom_permissions: {...} }
    Owner updates fine-grained permissions for a staff member.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    tenant_id = request.active_business['tenant_id']
    try:
        member = BusinessMember.objects.get(id=member_id, tenant_id=tenant_id)
    except BusinessMember.DoesNotExist:
        return JsonResponse({'error': 'Mwanachama hapatikani'}, status=404)

    old_permissions = member.custom_permissions
    new_permissions = data.get('custom_permissions', {})

    valid_keys = {
        'can_change_prices', 'can_give_discounts', 'can_void_sales',
        'can_view_profit', 'can_manage_staff', 'can_adjust_stock',
        'can_view_financial_reports', 'can_approve_orders'
    }
    filtered = {k: bool(v) for k, v in new_permissions.items() if k in valid_keys}

    member.custom_permissions = filtered
    member.save(update_fields=['custom_permissions'])

    log_action(
        action='PERMISSIONS_UPDATED',
        target_type='business_member',
        target_id=member.id,
        old_value=old_permissions,
        new_value=filtered,
        user_id=request.global_user['id'],
        user_name=request.global_user['full_name'],
        tenant_id=str(tenant_id),
    )

    return JsonResponse({'success': True, 'permissions': filtered})


@require_http_methods(["GET"])
def list_mini_apps(request):
    """GET /api/tenants/mini-apps/ — Public list of available mini-apps."""
    apps = MiniApp.objects.all().order_by('display_order')
    return JsonResponse({
        'mini_apps': [
            {
                'id': str(a.id),
                'name': a.name,
                'slug': a.slug,
                'icon': a.icon,
                'is_active': a.is_active,
                'is_coming_soon': a.is_coming_soon,
            }
            for a in apps
        ]
    })
