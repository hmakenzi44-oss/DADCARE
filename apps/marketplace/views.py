"""
marketplace/views.py — Public marketplace + tenant listing management.

Public routes (no auth):
  GET  /api/marketplace/           Browse approved listings
  GET  /api/marketplace/<id>/      Single listing detail

Tenant routes (require_business):
  POST /api/marketplace/listings/submit/    Submit a new listing
  GET  /api/marketplace/listings/mine/      My business listings
  DELETE /api/marketplace/listings/<id>/    Remove own listing
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from apps.marketplace.models import MarketplaceListing
from apps.core.permissions import require_business
from apps.core.audit_service import log_action
from apps.ai_moderation.gemini_service import moderate_listing


# ─────────────────────────────────────────────
# PUBLIC — No authentication required
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
def browse_marketplace(request):
    """
    GET /api/marketplace/
    Public listing browse. No login needed.
    Filters: category, city, country_code, search, mini_app, page
    """
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    city = request.GET.get('city', '').strip()
    country = request.GET.get('country_code', '').strip()
    mini_app = request.GET.get('mini_app', '').strip()
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 24
    offset = (page - 1) * per_page

    qs = MarketplaceListing.objects.filter(
        status__in=['approved', 'auto_approved']
    )

    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tenant_name__icontains=search)
        )
    if category:
        qs = qs.filter(category=category)
    if city:
        qs = qs.filter(city__icontains=city)
    if country:
        qs = qs.filter(country_code=country)
    if mini_app:
        qs = qs.filter(mini_app_id=mini_app)

    total = qs.count()
    listings = qs.order_by('-created_at')[offset:offset + per_page]

    return JsonResponse({
        'listings': [_serialize_public(l) for l in listings],
        'total': total,
        'page': page,
        'per_page': per_page,
    })


@require_http_methods(["GET"])
def listing_detail(request, listing_id):
    """GET /api/marketplace/<id>/ — Single listing. Public."""
    try:
        listing = MarketplaceListing.objects.get(
            id=listing_id,
            status__in=['approved', 'auto_approved']
        )
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Bidhaa haipatikani'}, status=404)

    return JsonResponse(_serialize_public(listing))


@require_http_methods(["GET"])
def marketplace_categories(request):
    """GET /api/marketplace/categories/ — Distinct categories in approved listings."""
    from django.db.models import Count
    cats = (
        MarketplaceListing.objects
        .filter(status__in=['approved', 'auto_approved'], category__gt='')
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')[:50]
    )
    return JsonResponse({'categories': list(cats)})


# ─────────────────────────────────────────────
# TENANT — Requires active business JWT
# ─────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
@require_business
def submit_listing(request):
    """
    POST /api/marketplace/listings/submit/
    Body: {
        title, description?, price?, currency?, category?,
        images?, contact_whatsapp?, contact_phone?, city?, country_code?
    }
    Runs Gemini moderation immediately — auto-approves if score >= 85.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Kichwa cha tangazo kinahitajika'}, status=400)

    business = request.active_business
    tenant_id = business['tenant_id']

    # Check listing limit (max 50 active per tenant)
    active_count = MarketplaceListing.objects.filter(
        tenant_id=tenant_id,
        status__in=['pending', 'approved', 'auto_approved']
    ).count()
    if active_count >= 50:
        return JsonResponse(
            {'error': 'Umefika kikomo cha matangazo 50. Futa baadhi kwanza.'},
            status=400
        )

    listing_data = {
        'title': title,
        'description': data.get('description', ''),
        'price': data.get('price'),
        'currency': data.get('currency', 'TZS'),
        'category': data.get('category', ''),
        'images': data.get('images', []),
        'city': data.get('city', ''),
        'country_code': data.get('country_code', ''),
    }

    # Run AI moderation
    moderation = moderate_listing(listing_data)

    listing = MarketplaceListing.objects.create(
        tenant_id=tenant_id,
        tenant_name=business['tenant_name'],
        title=title,
        description=listing_data['description'],
        price=listing_data['price'],
        currency=listing_data['currency'],
        category=listing_data['category'],
        images=listing_data['images'],
        contact_whatsapp=data.get('contact_whatsapp', ''),
        contact_phone=data.get('contact_phone', ''),
        city=listing_data['city'],
        country_code=listing_data['country_code'],
        ai_score=moderation['score'],
        ai_reason=moderation['reason'],
        status=moderation['status'],
        reviewed_at=timezone.now() if moderation['status'] != 'pending' else None,
    )

    log_action(
        action='LISTING_SUBMITTED',
        target_type='marketplace_listing',
        target_id=listing.id,
        new_value={
            'title': title,
            'ai_score': moderation['score'],
            'status': moderation['status'],
        },
        user_id=request.global_user['id'],
        user_name=request.global_user['full_name'],
        tenant_id=str(tenant_id),
    )

    return JsonResponse({
        'success': True,
        'listing_id': str(listing.id),
        'status': listing.status,
        'ai_score': listing.ai_score,
        'message': _status_message(listing.status),
    }, status=201)


@require_http_methods(["GET"])
@require_business
def my_listings(request):
    """GET /api/marketplace/listings/mine/ — This business's listings."""
    tenant_id = request.active_business['tenant_id']
    status_filter = request.GET.get('status', '')

    qs = MarketplaceListing.objects.filter(tenant_id=tenant_id)
    if status_filter:
        qs = qs.filter(status=status_filter)

    listings = qs.order_by('-created_at')[:100]

    return JsonResponse({
        'listings': [_serialize_tenant(l) for l in listings]
    })


@csrf_exempt
@require_http_methods(["PATCH"])
@require_business
def update_listing(request, listing_id):
    """
    PATCH /api/marketplace/listings/<id>/update/
    Re-submits for AI moderation on update.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    tenant_id = request.active_business['tenant_id']
    try:
        listing = MarketplaceListing.objects.get(id=listing_id, tenant_id=tenant_id)
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Tangazo halipatikani'}, status=404)

    allowed = ['title', 'description', 'price', 'currency', 'category',
               'images', 'contact_whatsapp', 'contact_phone', 'city', 'country_code']

    for field in allowed:
        if field in data:
            setattr(listing, field, data[field])

    # Re-run AI moderation
    moderation = moderate_listing({
        'title': listing.title,
        'description': listing.description,
        'price': listing.price,
        'currency': listing.currency,
        'category': listing.category,
        'images': listing.images,
        'city': listing.city,
        'country_code': listing.country_code,
    })

    listing.ai_score = moderation['score']
    listing.ai_reason = moderation['reason']
    listing.status = moderation['status']
    listing.reviewed_at = timezone.now() if moderation['status'] != 'pending' else None
    listing.save()

    return JsonResponse({
        'success': True,
        'status': listing.status,
        'ai_score': listing.ai_score,
        'message': _status_message(listing.status),
    })


@csrf_exempt
@require_http_methods(["DELETE"])
@require_business
def delete_listing(request, listing_id):
    """DELETE /api/marketplace/listings/<id>/ — Remove own listing."""
    tenant_id = request.active_business['tenant_id']
    try:
        listing = MarketplaceListing.objects.get(id=listing_id, tenant_id=tenant_id)
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Tangazo halipatikani'}, status=404)

    listing_title = listing.title
    listing.delete()

    log_action(
        action='LISTING_DELETED',
        target_type='marketplace_listing',
        target_id=listing_id,
        old_value={'title': listing_title},
        user_id=request.global_user['id'],
        user_name=request.global_user['full_name'],
        tenant_id=str(tenant_id),
    )

    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _serialize_public(listing) -> dict:
    """Public-safe serialization — contact info included, no tenant internals."""
    return {
        'id': str(listing.id),
        'title': listing.title,
        'description': listing.description,
        'price': float(listing.price) if listing.price else None,
        'currency': listing.currency,
        'category': listing.category,
        'images': listing.images,
        'contact_whatsapp': listing.contact_whatsapp,
        'contact_phone': listing.contact_phone,
        'city': listing.city,
        'country_code': listing.country_code,
        'seller': {
            'name': listing.tenant_name,
            'logo_url': listing.tenant_logo_url,
        },
        'created_at': listing.created_at.isoformat(),
    }


def _serialize_tenant(listing) -> dict:
    """Full serialization for tenant view — includes AI score and status."""
    data = _serialize_public(listing)
    data.update({
        'status': listing.status,
        'ai_score': listing.ai_score,
        'ai_reason': listing.ai_reason,
        'reviewed_at': listing.reviewed_at.isoformat() if listing.reviewed_at else None,
    })
    return data


def _status_message(status: str) -> str:
    messages = {
        'auto_approved': 'Tangazo lako limeidhinishwa moja kwa moja na AI.',
        'pending': 'Tangazo lako linasubiri ukaguzi wa mikono.',
        'auto_rejected': 'Tangazo lako limekataliwa. Tafadhali rekebisha na ujaribu tena.',
    }
    return messages.get(status, '')
