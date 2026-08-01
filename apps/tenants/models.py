"""
tenants/models.py — Multi-tenancy core (public schema).
Tenants, memberships, mini-apps, subscriptions, invite codes.
"""
import uuid
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.auth_app.models import GlobalUser


class MiniApp(BaseModel):
    """
    Registry of all mini-apps (Shop, School, Pharmacy, Gym, Marketplace).
    Activated per tenant by Super Admin — no code deployment needed.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=10)  # emoji
    version = models.CharField(max_length=20, default='1.0.0')
    is_active = models.BooleanField(default=False)
    is_coming_soon = models.BooleanField(default=True)
    feature_flags = models.JSONField(default=dict)
    display_order = models.IntegerField(default=0)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mini_apps'
        app_label = 'tenants'
        ordering = ['display_order']

    def __str__(self):
        return f"{self.icon} {self.name}"


class SubscriptionPlan(BaseModel):
    """Pricing plans per mini-app. Supports Pi and USDT payments."""
    mini_app = models.ForeignKey(
        MiniApp, on_delete=models.CASCADE,
        related_name='plans', null=True, blank=True
    )
    name = models.CharField(max_length=100)
    price_pi = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    price_usdt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration_days = models.IntegerField()
    max_users = models.IntegerField(default=10)
    max_products = models.IntegerField(default=500)
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscription_plans'
        app_label = 'tenants'

    def __str__(self):
        return f"{self.name} ({self.duration_days}d)"


class Tenant(BaseModel):
    """
    A business registered on DADCARE.
    Gets its own PostgreSQL schema: tenant_{id}
    Trial: 90 days hardcoded — NEVER configurable.
    """

    SUBSCRIPTION_STATUS = [
        ('trial', 'Trial'),
        ('trial_expired', 'Trial Expired'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    mini_app = models.ForeignKey(
        MiniApp, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tenants'
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    subscription_status = models.CharField(
        max_length=20, choices=SUBSCRIPTION_STATUS, default='trial'
    )
    trial_started_at = models.DateTimeField(auto_now_add=True)
    trial_expires_at = models.DateTimeField(null=True, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    logo_url = models.URLField(max_length=500, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    pi_wallet_address = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tenants'
        app_label = 'tenants'

    def __str__(self):
        return self.name

    @property
    def schema_name(self):
        """PostgreSQL schema name for this tenant."""
        return f"tenant_{self.id}"

    def save(self, *args, **kwargs):
        """Set trial_expires_at on creation using hardcoded TRIAL_DAYS."""
        if not self.pk and not self.trial_expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.trial_expires_at = timezone.now() + timedelta(
                days=getattr(settings, 'TRIAL_DAYS', 90)
            )
        super().save(*args, **kwargs)


class BusinessMember(BaseModel):
    """
    Links a GlobalUser to a Tenant with a role.
    One user can belong to many businesses with different roles.
    """

    ROLES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ]

    global_user = models.ForeignKey(
        GlobalUser, on_delete=models.CASCADE,
        related_name='memberships'
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(max_length=20, choices=ROLES)
    # Owner can grant fine-grained permissions per employee
    custom_permissions = models.JSONField(default=dict)
    # Structure:
    # {
    #   "can_change_prices": bool,
    #   "can_give_discounts": bool,
    #   "can_void_sales": bool,
    #   "can_view_profit": bool,
    #   "can_manage_staff": bool,
    #   "can_adjust_stock": bool,
    #   "can_view_financial_reports": bool,
    #   "can_approve_orders": bool
    # }
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        GlobalUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invited_members'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'business_members'
        app_label = 'tenants'
        unique_together = ('global_user', 'tenant')

    def __str__(self):
        return f"{self.global_user.full_name} @ {self.tenant.name} [{self.role}]"

    def has_permission(self, permission_key: str) -> bool:
        """Check custom permission; owners have all permissions."""
        if self.role == 'owner':
            return True
        return self.custom_permissions.get(permission_key, False)


class InviteCode(BaseModel):
    """
    One-time (or limited-use) invite code to join a business.
    Expires in 7 days. Carries the role + custom permissions.
    """
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE,
        related_name='invite_codes'
    )
    created_by = models.ForeignKey(
        GlobalUser, on_delete=models.CASCADE,
        related_name='created_invites'
    )
    role = models.CharField(max_length=20)
    custom_permissions = models.JSONField(default=dict)
    code = models.CharField(max_length=20, unique=True)
    max_uses = models.IntegerField(default=1)
    uses = models.IntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'invite_codes'
        app_label = 'tenants'

    def __str__(self):
        return f"Invite {self.code} → {self.tenant.name}"

    @property
    def is_valid(self):
        from django.utils import timezone
        return self.uses < self.max_uses and self.expires_at > timezone.now()


class SubscriptionPayment(BaseModel):
    """
    Payment records for subscriptions (Pi or USDT).
    Super Admin confirms manually — no auto-confirmation.
    """

    PAYMENT_TYPES = [('pi', 'Pi Network'), ('usdt', 'USDT TRC-20')]
    STATUSES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE,
        related_name='payments'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True
    )
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=4)
    transaction_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expiry_granted = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'subscription_payments'
        app_label = 'tenants'

    def __str__(self):
        return f"{self.tenant.name} — {self.payment_type} {self.amount} [{self.status}]"


class CryptoSetting(BaseModel):
    """Super Admin's active crypto wallet addresses."""
    WALLET_TYPES = [('pi', 'Pi Network'), ('usdt', 'USDT')]

    wallet_type = models.CharField(max_length=10, choices=WALLET_TYPES)
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=20, blank=True)  # TRC20 for USDT
    is_active = models.BooleanField(default=True)
    changed_at = models.DateTimeField(auto_now=True)
    previous_address = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'crypto_settings'
        app_label = 'tenants'

    def __str__(self):
        return f"{self.wallet_type} — {self.address[:20]}..."
