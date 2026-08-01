"""
ai_moderation/views.py — Internal AI moderation endpoints.
Used by Super Admin panel to re-moderate, review queue, and override decisions.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.marketplace.models import MarketplaceListing
from apps.ai_moderation.gemini_service import moderate_listing
from apps.core.audit_service import log_action
from django.utils import timezone


def _require_super_admin(view_func):
    """Simple guard — Super Admin auth handled in Step 6."""
    import functools
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Placeholder — replaced by real Super Admin JWT check in Step 6
        if not getattr(request, 'is_super_admin', False):
            return JsonResponse({'error': 'Super Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@require_http_methods(["GET"])
def moderation_queue(request):
    """
    GET /api/ai/queue/
    Returns pending listings awaiting manual review (score 50-84).
    Public for now — locked by Super Admin middleware in Step 6.
    """
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 20

    pending = MarketplaceListing.objects.filter(
        status='pending'
    ).order_by('created_at')

    total = pending.count()
    listings = pending[(page - 1) * per_page: page * per_page]

    return JsonResponse({
        'pending_count': total,
        'listings': [_serialize_for_review(l) for l in listings],
        'page': page,
    })


@csrf_exempt
@require_http_methods(["POST"])
def manual_review(request, listing_id):
    """
    POST /api/ai/review/<id>/
    Body: { decision: "approved"|"rejected", reason? }
    Super Admin manually approves or rejects a pending listing.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    decision = data.get('decision', '')
    if decision not in ('approved', 'rejected'):
        return JsonResponse({'error': 'decision lazima iwe approved au rejected'}, status=400)

    try:
        listing = MarketplaceListing.objects.get(id=listing_id)
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Tangazo halipatikani'}, status=404)

    old_status = listing.status
    listing.status = decision
    listing.ai_reason = data.get('reason', listing.ai_reason)
    listing.reviewed_at = timezone.now()
    listing.save(update_fields=['status', 'ai_reason', 'reviewed_at'])

    log_action(
        action='LISTING_MANUALLY_REVIEWED',
        target_type='marketplace_listing',
        target_id=listing.id,
        old_value={'status': old_status},
        new_value={'status': decision, 'reason': data.get('reason', '')},
    )

    return JsonResponse({'success': True, 'listing_id': str(listing.id), 'status': decision})


@csrf_exempt
@require_http_methods(["POST"])
def remoderate_listing(request, listing_id):
    """
    POST /api/ai/remoderate/<id>/
    Re-runs Gemini moderation on an existing listing.
    """
    try:
        listing = MarketplaceListing.objects.get(id=listing_id)
    except MarketplaceListing.DoesNotExist:
        return JsonResponse({'error': 'Tangazo halipatikani'}, status=404)

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

    old_status = listing.status
    listing.ai_score = moderation['score']
    listing.ai_reason = moderation['reason']
    listing.status = moderation['status']
    listing.reviewed_at = timezone.now()
    listing.save(update_fields=['ai_score', 'ai_reason', 'status', 'reviewed_at'])

    log_action(
        action='LISTING_REMODERATED',
        target_type='marketplace_listing',
        target_id=listing.id,
        old_value={'status': old_status},
        new_value={'status': moderation['status'], 'score': moderation['score']},
    )

    return JsonResponse({
        'success': True,
        'ai_score': moderation['score'],
        'status': moderation['status'],
        'reason': moderation['reason'],
    })


def _serialize_for_review(listing) -> dict:
    return {
        'id': str(listing.id),
        'title': listing.title,
        'description': listing.description[:300],
        'price': float(listing.price) if listing.price else None,
        'currency': listing.currency,
        'category': listing.category,
        'images': listing.images,
        'city': listing.city,
        'country_code': listing.country_code,
        'tenant_name': listing.tenant_name,
        'ai_score': listing.ai_score,
        'ai_reason': listing.ai_reason,
        'contact_whatsapp': listing.contact_whatsapp,
        'contact_phone': listing.contact_phone,
        'submitted_at': listing.created_at.isoformat(),
    }
