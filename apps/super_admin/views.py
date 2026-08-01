"""
super_admin/views.py — Control panel for DADCARE Super Admin.
All routes live at control.dadcare.app — never exposed on main domain.
TOTP 2FA required after password login.
"""
import json
import hashlib
import secrets
from datetime import timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Sum, Q

from apps.super_admin.models import SuperAdminUser, SuperAdminSession
from apps.super_admin.jwt_service import create_sa_jwt, set_sa_cookie, clear_sa_cookie, SA_EXPIRY
from apps.super_admin.middleware import require_super_admin
from apps.super_admin.totp_service import (
    generate_totp_secret, get_totp_uri, verify_totp, generate_qr_data_url
)
from apps.tenants.models import Tenant, BusinessMember, MiniApp, SubscriptionPayment
from apps.marketplace.models import MarketplaceListing
from apps.core.models import AuditLog
from apps.core.audit_service import log_action
from apps.auth_app.models import GlobalUser


def _hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{pw}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split(':', 1)
        return hashlib.sha256(f"{salt}{pw}".encode()).hexdigest() == h
    except ValueError:
        return False


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def sa_login_step1(request):
    """
    POST /sa/auth/login/
    Step 1: email + password → returns totp_required flag.
    Does NOT issue JWT yet — TOTP verification in step 2.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    try:
        admin = SuperAdminUser.objects.get(email=email, is_active=True)
    except SuperAdminUser.DoesNotExist:
        return JsonResponse({'error': 'Credentials si sahihi'}, status=401)

    if not _verify_password(password, admin.password_hash):
        return JsonResponse({'error': 'Credentials si sahihi'}, status=401)

    # Issue a short-lived pre-auth token stored in session (not cookie)
    # We use a signed temp token to carry the admin_id into step 2
    pre_auth = secrets.token_urlsafe(32)
    # Store in a simple dict — in production use Redis/cache
    _PRE_AUTH_STORE[pre_auth] = {
        'admin_id': str(admin.id),
        'expires': timezone.now() + timedelta(minutes=5),
    }

    return JsonResponse({
        'totp_required': admin.totp_enabled,
        'pre_auth_token': pre_auth,
        'message': 'Ingiza nambari ya Google Authenticator' if admin.totp_enabled else 'TOTP haijawezeshwa',
    })


# Simple in-memory store for pre-auth tokens (replace with Redis in production)
_PRE_AUTH_STORE: dict = {}


@csrf_exempt
@require_http_methods(["POST"])
def sa_login_step2(request):
    """
    POST /sa/auth/verify-totp/
    Step 2: pre_auth_token + totp_code → issues Super Admin JWT.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    pre_auth = data.get('pre_auth_token', '')
    totp_code = data.get('totp_code', '')

    stored = _PRE_AUTH_STORE.get(pre_auth)
    if not stored or stored['expires'] < timezone.now():
        _PRE_AUTH_STORE.pop(pre_auth, None)
        return JsonResponse({'error': 'Token imekwisha. Ingia upya.'}, status=401)

    admin = SuperAdminUser.objects.get(id=stored['admin_id'])

    if admin.totp_enabled:
        if not verify_totp(admin.totp_secret, totp_code):
            return JsonResponse({'error': 'Nambari ya TOTP si sahihi'}, status=401)

    # Clean up pre-auth token
    _PRE_AUTH_STORE.pop(pre_auth, None)

    # Issue JWT and create session record
    token = create_sa_jwt(admin)
    import jwt as pyjwt
    from django.conf import settings
    secret = getattr(settings, 'SA_JWT_SECRET', settings.JWT_SECRET + '_sa')
    payload = pyjwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    SuperAdminSession.objects.create(
        admin=admin,
        token_jti=payload['jti'],
        ip_address=ip or None,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + SA_EXPIRY,
    )

    admin.last_login = timezone.now()
    admin.save(update_fields=['last_login'])

    log_action(
        action='SUPER_ADMIN_LOGIN',
        target_type='super_admin_user',
        target_id=admin.id,
        user_id=str(admin.id),
        user_name=admin.email,
    )

    response = JsonResponse({
        'success': True,
        'admin': {'id': str(admin.id), 'email': admin.email, 'full_name': admin.full_name},
    })
    set_sa_cookie(response, token)
    return response


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def sa_logout(request):
    """POST /sa/auth/logout/ — Revoke session and clear cookie."""
    jti = request.super_admin['jti']
    SuperAdminSession.objects.filter(token_jti=jti).update(is_revoked=True)
    response = JsonResponse({'success': True})
    clear_sa_cookie(response)
    return response


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def setup_totp(request):
    """
    POST /sa/auth/setup-totp/
    Generates a new TOTP secret and returns QR code.
    Must be confirmed with verify-totp before being activated.
    """
    admin = SuperAdminUser.objects.get(id=request.super_admin['id'])
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, admin.email)
    qr_data_url = generate_qr_data_url(uri)

    # Store pending secret — activated only after verification
    admin.totp_secret = secret
    admin.totp_enabled = False
    admin.save(update_fields=['totp_secret', 'totp_enabled'])

    return JsonResponse({
        'totp_uri': uri,
        'qr_code': qr_data_url,
        'message': 'Scan QR code na Google Authenticator, kisha thibitisha.',
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def confirm_totp(request):
    """POST /sa/auth/confirm-totp/ — Body: { code } — Activates TOTP."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    admin = SuperAdminUser.objects.get(id=request.super_admin['id'])
    code = data.get('code', '')

    if not verify_totp(admin.totp_secret, code):
        return JsonResponse({'error': 'Nambari si sahihi. Jaribu tena.'}, status=400)

    admin.totp_enabled = True
    admin.save(update_fields=['totp_enabled'])

    return JsonResponse({'success': True, 'message': 'TOTP imewezeshwa.'})


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def sa_dashboard(request):
    """GET /sa/dashboard/ — Platform-wide KPIs."""
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    trial_tenants = Tenant.objects.filter(subscription_status='trial').count()
    paying_tenants = Tenant.objects.filter(subscription_status='active').count()
    expired_tenants = Tenant.objects.filter(
        subscription_status__in=['trial_expired', 'expired']
    ).count()

    total_users = GlobalUser.objects.count()
    new_users_today = GlobalUser.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    pending_listings = MarketplaceListing.objects.filter(status='pending').count()
    total_listings = MarketplaceListing.objects.filter(
        status__in=['approved', 'auto_approved']
    ).count()

    pending_payments = SubscriptionPayment.objects.filter(status='pending').count()
    revenue_confirmed = SubscriptionPayment.objects.filter(
        status='confirmed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Tenants expiring in next 7 days
    expiring_soon = Tenant.objects.filter(
        subscription_status='trial',
        trial_expires_at__lte=timezone.now() + timedelta(days=7),
        trial_expires_at__gte=timezone.now(),
    ).count()

    return JsonResponse({
        'tenants': {
            'total': total_tenants,
            'active': active_tenants,
            'trial': trial_tenants,
            'paying': paying_tenants,
            'expired': expired_tenants,
            'expiring_soon_7d': expiring_soon,
        },
        'users': {
            'total': total_users,
            'new_today': new_users_today,
        },
        'marketplace': {
            'pending_review': pending_listings,
            'total_approved': total_listings,
        },
        'subscriptions': {
            'pending_payments': pending_payments,
            'total_revenue_usdt': float(revenue_confirmed),
        },
    })


# ─────────────────────────────────────────────
# TENANT MANAGEMENT
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def list_tenants(request):
    """GET /sa/tenants/ — All tenants with filters."""
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 30

    qs = Tenant.objects.all()
    if status:
        qs = qs.filter(subscription_status=status)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

    total = qs.count()
    tenants = qs.order_by('-created_at')[(page-1)*per_page: page*per_page]

    return JsonResponse({
        'tenants': [_serialize_tenant(t) for t in tenants],
        'total': total,
        'page': page,
    })


@require_http_methods(["GET"])
@require_super_admin
def tenant_detail(request, tenant_id):
    """GET /sa/tenants/<id>/ — Full tenant detail with member count."""
    try:
        tenant = Tenant.objects.select_related('mini_app', 'subscription_plan').get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant haipatikani'}, status=404)

    member_count = BusinessMember.objects.filter(tenant=tenant, is_active=True).count()
    payment_history = SubscriptionPayment.objects.filter(
        tenant=tenant
    ).order_by('-created_at')[:10]

    return JsonResponse({
        'tenant': _serialize_tenant(tenant),
        'member_count': member_count,
        'payment_history': [_serialize_payment(p) for p in payment_history],
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_super_admin
def update_tenant(request, tenant_id):
    """
    PATCH /sa/tenants/<id>/update/
    Super Admin can: suspend, reactivate, add notes, extend trial.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant haipatikani'}, status=404)

    old_status = tenant.subscription_status
    allowed = ['is_active', 'admin_notes', 'subscription_status']
    updated = {}

    for field in allowed:
        if field in data:
            setattr(tenant, field, data[field])
            updated[field] = data[field]

    # Extend trial by N days
    if 'extend_trial_days' in data:
        from datetime import timedelta
        days = int(data['extend_trial_days'])
        base = tenant.trial_expires_at or timezone.now()
        tenant.trial_expires_at = base + timedelta(days=days)
        updated['trial_extended_by_days'] = days

    if updated:
        tenant.save()
        log_action(
            action='TENANT_UPDATED_BY_SA',
            target_type='tenant',
            target_id=tenant.id,
            old_value={'status': old_status},
            new_value=updated,
            user_id=request.super_admin['id'],
            user_name=request.super_admin['email'],
        )

    return JsonResponse({'success': True, 'updated': updated})


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def suspend_tenant(request, tenant_id):
    """POST /sa/tenants/<id>/suspend/ — Immediately suspend a tenant."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant haipatikani'}, status=404)

    reason = data.get('reason', '').strip()
    tenant.subscription_status = 'suspended'
    tenant.is_active = False
    tenant.admin_notes = f"Suspended: {reason}" if reason else tenant.admin_notes
    tenant.save(update_fields=['subscription_status', 'is_active', 'admin_notes'])

    log_action(
        action='TENANT_SUSPENDED',
        target_type='tenant',
        target_id=tenant.id,
        new_value={'reason': reason},
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
        tenant_id=str(tenant.id),
    )

    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def reactivate_tenant(request, tenant_id):
    """POST /sa/tenants/<id>/reactivate/"""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({'error': 'Tenant haipatikani'}, status=404)

    tenant.subscription_status = 'active'
    tenant.is_active = True
    tenant.save(update_fields=['subscription_status', 'is_active'])

    log_action(
        action='TENANT_REACTIVATED',
        target_type='tenant',
        target_id=tenant.id,
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
        tenant_id=str(tenant.id),
    )
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# SUBSCRIPTION PAYMENTS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def list_payments(request):
    """GET /sa/payments/ — All subscription payment records."""
    status = request.GET.get('status', 'pending')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 30

    qs = SubscriptionPayment.objects.select_related('tenant', 'plan')
    if status:
        qs = qs.filter(status=status)

    total = qs.count()
    payments = qs.order_by('-created_at')[(page-1)*per_page: page*per_page]

    return JsonResponse({
        'payments': [_serialize_payment(p) for p in payments],
        'total': total,
        'page': page,
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def confirm_payment(request, payment_id):
    """
    POST /sa/payments/<id>/confirm/
    Body: { expiry_days? }  — defaults to plan duration
    Confirms a payment and activates/extends the tenant subscription.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    try:
        payment = SubscriptionPayment.objects.select_related('tenant', 'plan').get(id=payment_id)
    except SubscriptionPayment.DoesNotExist:
        return JsonResponse({'error': 'Malipo haipatikani'}, status=404)

    if payment.status == 'confirmed':
        return JsonResponse({'error': 'Malipo haya tayari yamethibitishwa'}, status=400)

    # Calculate expiry
    duration = data.get('expiry_days') or (payment.plan.duration_days if payment.plan else 30)
    now = timezone.now()
    tenant = payment.tenant
    base = max(tenant.subscription_expires_at or now, now)
    new_expiry = base + timedelta(days=duration)

    payment.status = 'confirmed'
    payment.confirmed_at = now
    payment.expiry_granted = new_expiry
    payment.save(update_fields=['status', 'confirmed_at', 'expiry_granted'])

    tenant.subscription_status = 'active'
    tenant.subscription_expires_at = new_expiry
    tenant.is_active = True
    tenant.save(update_fields=['subscription_status', 'subscription_expires_at', 'is_active'])

    log_action(
        action='PAYMENT_CONFIRMED',
        target_type='subscription_payment',
        target_id=payment.id,
        new_value={
            'amount': str(payment.amount),
            'type': payment.payment_type,
            'expiry': new_expiry.isoformat(),
        },
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
        tenant_id=str(tenant.id),
    )

    return JsonResponse({
        'success': True,
        'tenant': tenant.name,
        'subscription_expires_at': new_expiry.isoformat(),
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def reject_payment(request, payment_id):
    """POST /sa/payments/<id>/reject/ — Body: { reason }"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        payment = SubscriptionPayment.objects.get(id=payment_id)
    except SubscriptionPayment.DoesNotExist:
        return JsonResponse({'error': 'Malipo haipatikani'}, status=404)

    payment.status = 'rejected'
    payment.save(update_fields=['status'])

    log_action(
        action='PAYMENT_REJECTED',
        target_type='subscription_payment',
        target_id=payment.id,
        new_value={'reason': data.get('reason', '')},
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
    )
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# MINI-APP FEATURE FLAGS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def list_mini_apps(request):
    """GET /sa/mini-apps/ — All mini-apps with activation status."""
    apps = MiniApp.objects.all().order_by('display_order')
    return JsonResponse({
        'mini_apps': [
            {
                'id': str(a.id),
                'name': a.name,
                'slug': a.slug,
                'icon': a.icon,
                'version': a.version,
                'is_active': a.is_active,
                'is_coming_soon': a.is_coming_soon,
                'feature_flags': a.feature_flags,
                'display_order': a.display_order,
                'tenant_count': Tenant.objects.filter(mini_app=a).count(),
            }
            for a in apps
        ]
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_super_admin
def update_mini_app(request, app_id):
    """
    PATCH /sa/mini-apps/<id>/
    Toggle is_active, is_coming_soon, update feature_flags.
    New mini-apps activated here — ZERO impact on existing tenants.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        app = MiniApp.objects.get(id=app_id)
    except MiniApp.DoesNotExist:
        return JsonResponse({'error': 'Mini-app haipatikani'}, status=404)

    old_state = {'is_active': app.is_active, 'is_coming_soon': app.is_coming_soon}
    allowed = ['is_active', 'is_coming_soon', 'feature_flags', 'display_order', 'version']
    updated = {}

    for field in allowed:
        if field in data:
            setattr(app, field, data[field])
            updated[field] = data[field]

    if 'is_active' in data and data['is_active']:
        app.is_coming_soon = False
        app.released_at = app.released_at or timezone.now()
        updated['is_coming_soon'] = False

    if updated:
        app.save()
        log_action(
            action='MINI_APP_UPDATED',
            target_type='mini_app',
            target_id=app.id,
            old_value=old_state,
            new_value=updated,
            user_id=request.super_admin['id'],
            user_name=request.super_admin['email'],
        )

    return JsonResponse({'success': True, 'updated': updated})


# ─────────────────────────────────────────────
# MARKETPLACE MODERATION QUEUE
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def sa_moderation_queue(request):
    """GET /sa/moderation/ — Pending listings for manual review."""
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 20

    pending = MarketplaceListing.objects.filter(status='pending').order_by('created_at')
    total = pending.count()
    listings = pending[(page-1)*per_page: page*per_page]

    return JsonResponse({
        'pending_count': total,
        'listings': [
            {
                'id': str(l.id),
                'title': l.title,
                'description': l.description[:300],
                'price': float(l.price) if l.price else None,
                'currency': l.currency,
                'category': l.category,
                'images': l.images,
                'city': l.city,
                'country_code': l.country_code,
                'tenant_name': l.tenant_name,
                'ai_score': l.ai_score,
                'ai_reason': l.ai_reason,
                'contact_whatsapp': l.contact_whatsapp,
                'contact_phone': l.contact_phone,
                'submitted_at': l.created_at.isoformat(),
            }
            for l in listings
        ],
        'page': page,
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_super_admin
def sa_review_listing(request, listing_id):
    """POST /sa/moderation/<id>/review/ — Body: { decision, reason? }"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    decision = data.get('decision', '')
    if decision not in ('approved', 'rejected'):
        return JsonResponse({'error': 'decision: approved au rejected'}, status=400)

    try:
        listing = MarketplaceListing.objects.get(id=listing_id)
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Tangazo halipatikani'}, status=404)

    listing.status = decision
    listing.ai_reason = data.get('reason', listing.ai_reason)
    listing.reviewed_at = timezone.now()
    listing.save(update_fields=['status', 'ai_reason', 'reviewed_at'])

    log_action(
        action=f'LISTING_{decision.upper()}_BY_SA',
        target_type='marketplace_listing',
        target_id=listing.id,
        new_value={'decision': decision, 'reason': data.get('reason', '')},
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
    )

    return JsonResponse({'success': True, 'status': decision})


# ─────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def audit_log(request):
    """GET /sa/audit/ — Immutable global audit log."""
    tenant_id = request.GET.get('tenant_id', '')
    action = request.GET.get('action', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 50

    qs = AuditLog.objects.all()
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if action:
        qs = qs.filter(action__icontains=action)

    total = qs.count()
    logs = qs.order_by('-created_at')[(page-1)*per_page: page*per_page]

    return JsonResponse({
        'logs': [
            {
                'id': str(l.id),
                'tenant_id': str(l.tenant_id) if l.tenant_id else None,
                'user_id': str(l.user_id) if l.user_id else None,
                'user_name': l.user_name,
                'action': l.action,
                'target_type': l.target_type,
                'target_id': str(l.target_id) if l.target_id else None,
                'old_value': l.old_value,
                'new_value': l.new_value,
                'ip_address': l.ip_address,
                'created_at': l.created_at.isoformat(),
            }
            for l in logs
        ],
        'total': total,
        'page': page,
    })


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_super_admin
def list_users(request):
    """GET /sa/users/ — All registered global users."""
    search = request.GET.get('search', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 50

    qs = GlobalUser.objects.all()
    if search:
        qs = qs.filter(Q(email__icontains=search) | Q(full_name__icontains=search))

    total = qs.count()
    users = qs.order_by('-created_at')[(page-1)*per_page: page*per_page]

    return JsonResponse({
        'users': [
            {
                'id': str(u.id),
                'email': u.email,
                'full_name': u.full_name,
                'is_active': u.is_active,
                'language': u.language,
                'country_code': u.country_code,
                'created_at': u.created_at.isoformat(),
                'last_login': u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        'total': total,
        'page': page,
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_super_admin
def toggle_user(request, user_id):
    """PATCH /sa/users/<id>/toggle/ — Activate/deactivate a global user."""
    try:
        user = GlobalUser.objects.get(id=user_id)
    except GlobalUser.DoesNotExist:
        return JsonResponse({'error': 'Mtumiaji hapatikani'}, status=404)

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])

    log_action(
        action='USER_TOGGLED',
        target_type='global_user',
        target_id=user.id,
        new_value={'is_active': user.is_active},
        user_id=request.super_admin['id'],
        user_name=request.super_admin['email'],
    )
    return JsonResponse({'success': True, 'is_active': user.is_active})


# ─────────────────────────────────────────────
# SERIALIZERS
# ─────────────────────────────────────────────

def _serialize_tenant(t) -> dict:
    return {
        'id': str(t.id),
        'name': t.name,
        'slug': t.slug,
        'mini_app': t.mini_app.name if t.mini_app else None,
        'subscription_status': t.subscription_status,
        'trial_expires_at': t.trial_expires_at.isoformat() if t.trial_expires_at else None,
        'subscription_expires_at': t.subscription_expires_at.isoformat() if t.subscription_expires_at else None,
        'is_active': t.is_active,
        'city': t.city,
        'country_code': t.country_code,
        'phone': t.phone,
        'whatsapp': t.whatsapp,
        'admin_notes': t.admin_notes,
        'created_at': t.created_at.isoformat(),
    }


def _serialize_payment(p) -> dict:
    return {
        'id': str(p.id),
        'tenant': p.tenant.name if p.tenant else None,
        'tenant_id': str(p.tenant_id) if p.tenant_id else None,
        'payment_type': p.payment_type,
        'amount': float(p.amount),
        'transaction_reference': p.transaction_reference,
        'status': p.status,
        'confirmed_at': p.confirmed_at.isoformat() if p.confirmed_at else None,
        'expiry_granted': p.expiry_granted.isoformat() if p.expiry_granted else None,
        'created_at': p.created_at.isoformat(),
    }
