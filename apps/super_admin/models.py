"""
super_admin/models.py — Super Admin identity (public schema).
Completely separate from GlobalUser — different table, different JWT, different auth flow.
Only accessible at control.dadcare.app.
TOTP (Google Authenticator) required after password login.
"""
import uuid
from django.db import models
from apps.core.models import BaseModel


class SuperAdminUser(BaseModel):
    """
    One record per Super Admin.
    Created via management command only — no registration endpoint.
    """
    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255)
    totp_secret = models.CharField(max_length=64, blank=True)
    totp_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'super_admin_users'
        app_label = 'super_admin'

    def __str__(self):
        return f"SuperAdmin: {self.email}"


class SuperAdminSession(BaseModel):
    """
    Tracks active Super Admin sessions for audit purposes.
    Separate from JWT — allows forced logout from panel.
    """
    admin = models.ForeignKey(
        SuperAdminUser, on_delete=models.CASCADE,
        related_name='sessions'
    )
    token_jti = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'super_admin_sessions'
        app_label = 'super_admin'
        indexes = [models.Index(fields=['token_jti'])]
