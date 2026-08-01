"""
ai_moderation/gemini_service.py — Google Gemini Flash 2.0 integration.
Scores marketplace listings: >=85 auto-approve, 50-84 manual, <50 auto-reject.
"""
import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure Gemini on module load
genai.configure(api_key=settings.GEMINI_API_KEY)


MODERATION_PROMPT = """
You are a marketplace content moderator for DADCARE, a business platform serving East and Southern Africa.

Evaluate this marketplace listing and return a JSON object ONLY — no explanation, no markdown.

Score the listing from 0 to 100 based on:
- Content quality and completeness (title, description, price, images)
- Appropriateness for a general business marketplace
- No prohibited content (weapons, drugs, adult content, scams, stolen goods)
- No misleading claims or fake prices
- Relevance to legitimate business (retail, wholesale, pharmacy, services)

AUTO-APPROVE threshold: 85+ (clear, complete, legitimate listing)
MANUAL REVIEW threshold: 50-84 (acceptable but needs human check)
AUTO-REJECT threshold: below 50 (prohibited, incomplete, or suspicious)

Listing to evaluate:
Title: {title}
Description: {description}
Category: {category}
Price: {price} {currency}
City: {city}
Country: {country}
Number of images: {image_count}

Return ONLY this JSON:
{{
  "score": <integer 0-100>,
  "reason": "<one sentence explanation in English>",
  "flags": ["<flag1>", "<flag2>"]
}}

Flags may include: "incomplete_description", "no_images", "suspicious_price",
"prohibited_content", "spam", "misleading", "excellent_listing"
"""


def moderate_listing(listing_data: dict) -> dict:
    """
    Send a listing to Gemini for moderation scoring.
    Returns: { score, reason, flags, status }
    Falls back to manual review on any API error.
    """
    prompt = MODERATION_PROMPT.format(
        title=listing_data.get('title', ''),
        description=listing_data.get('description', '')[:500],
        category=listing_data.get('category', 'General'),
        price=listing_data.get('price', 'Not specified'),
        currency=listing_data.get('currency', 'TZS'),
        city=listing_data.get('city', ''),
        country=listing_data.get('country_code', ''),
        image_count=len(listing_data.get('images', [])),
    )

    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=256,
            )
        )

        raw = response.text.strip()
        # Strip markdown fences if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        score = int(result.get('score', 50))
        reason = result.get('reason', '')
        flags = result.get('flags', [])

    except json.JSONDecodeError as e:
        logger.error(f"Gemini JSON parse error: {e} — raw: {response.text[:200]}")
        return _fallback_result('JSON parse error')
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return _fallback_result(str(e))

    # Determine status from score
    if score >= 85:
        status = 'auto_approved'
    elif score >= 50:
        status = 'pending'  # Manual review
    else:
        status = 'auto_rejected'

    return {
        'score': score,
        'reason': reason,
        'flags': flags,
        'status': status,
    }


def _fallback_result(error_msg: str) -> dict:
    """On Gemini failure, fall back to manual review — never block a listing."""
    return {
        'score': None,
        'reason': f'AI moderation unavailable: {error_msg}',
        'flags': ['ai_unavailable'],
        'status': 'pending',
    }


def moderate_batch(listings: list[dict]) -> list[dict]:
    """Moderate multiple listings. Used by Super Admin bulk-remoderate action."""
    return [moderate_listing(l) for l in listings]
