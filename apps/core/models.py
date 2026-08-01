"""
core/models.py — Shared abstract base models + AuditLog (public schema).
"""
import uuid
from django.db import models


class UUIDModel(models.Model):
    """Abstract base: UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract base: created_at + updated_at."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Combined abstract base for all DADCARE public-schema models."""
    class Meta:
        abstract = True


class AuditLog(UUIDModel):
    """
    IMMUTABLE global audit log in public schema.
    PostgreSQL trigger blocks all UPDATE/DELETE.
    Written to via AuditService — never directly.
    """
    tenant_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    user_name = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        app_label = 'core'
        indexes = [
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['user_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"[{self.action}] {self.user_name} → {self.target_type} {self.target_id}"
