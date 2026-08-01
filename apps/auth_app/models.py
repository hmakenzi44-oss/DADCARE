"""
auth_app/models.py — Global user identity (public schema).
One GlobalUser = one real person. Can belong to many businesses.
"""
import uuid
from django.db import models
from apps.core.models import BaseModel


class GlobalUser(BaseModel):
    """
    Single global identity per real person.
    Lives in public schema — NOT duplicated per tenant.
    """
    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255)
    language = models.CharField(max_length=5, default='en')
    country_code = models.CharField(max_length=5, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'global_users'
        app_label = 'auth_app'

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class RevokedToken(BaseModel):
    """
    Blacklisted JWTs — checked on every authenticated request.
    Used for immediate employee removal without waiting for token expiry.
    """
    token_jti = models.CharField(max_length=255, unique=True)
    global_user = models.ForeignKey(
        GlobalUser, on_delete=models.CASCADE,
        related_name='revoked_tokens', null=True, blank=True
    )
    tenant_id = models.UUIDField(null=True, blank=True)
    revoked_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'revoked_tokens'
        app_label = 'auth_app'
        indexes = [
            models.Index(fields=['token_jti']),
        ]

    def __str__(self):
        return f"Revoked: {self.token_jti[:20]}..."
