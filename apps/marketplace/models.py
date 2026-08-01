"""
marketplace/models.py — Public marketplace listings (public schema).
NO sensitive tenant data here — only what buyers need to contact sellers.
AI moderation scores: >=85 auto-approve, 50-84 manual, <50 auto-reject.
"""
import uuid
from django.db import models
from apps.core.models import BaseModel


class MarketplaceListing(BaseModel):
    """
    Public product/service listings from any tenant.
    Contact is WhatsApp/Phone ONLY — no cart, no checkout.
    """

    STATUSES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto-Approved (AI >= 85)'),
        ('auto_rejected', 'Auto-Rejected (AI < 50)'),
    ]

    # Tenant reference (denormalized for performance — public schema query)
    tenant_id = models.UUIDField()
    mini_app_id = models.UUIDField(null=True, blank=True)
    tenant_name = models.CharField(max_length=255)
    tenant_logo_url = models.URLField(max_length=500, blank=True)

    # Listing content
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='TZS')
    category = models.CharField(max_length=100, blank=True)
    images = models.JSONField(default=list)  # List of Cloudinary URLs

    # Contact (WhatsApp/Phone ONLY — no cart)
    contact_whatsapp = models.CharField(max_length=50, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Location
    city = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, blank=True)

    # AI moderation
    ai_score = models.IntegerField(null=True, blank=True)
    ai_reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'marketplace_listings'
        app_label = 'marketplace'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['tenant_id']),
            models.Index(fields=['category']),
            models.Index(fields=['country_code', 'city']),
        ]

    def __str__(self):
        return f"{self.title} — {self.tenant_name} [{self.status}]"

    @property
    def is_visible(self):
        return self.status in ('approved', 'auto_approved')
