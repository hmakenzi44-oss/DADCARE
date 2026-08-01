"""
shop/models.py — Shop mini-app models (tenant schema).
These tables live in tenant_{uuid} schema, NOT in public.
Django uses unmanaged models with db_table set to the table name only
(schema is set via search_path in TenantMiddleware).

IMPORTANT: These models use managed=False in Meta — migrations create them
via raw SQL executed per-tenant on signup, not via Django's migration system.
"""
import uuid
from django.db import models
from apps.core.models import UUIDModel


class ShopSettings(UUIDModel):
    """Per-tenant shop configuration."""
    shop_name = models.CharField(max_length=255)
    logo_url = models.URLField(max_length=500, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=5, default='sw')
    currency = models.CharField(max_length=10, default='TZS')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    receipt_footer = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_settings'
        app_label = 'shop'
        managed = False


class Category(UUIDModel):
    """Product categories (tenant-scoped)."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        app_label = 'shop'
        managed = False
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(UUIDModel):
    """
    Products in the tenant's inventory.
    Low stock alert when stock_quantity <= low_stock_threshold.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    unit = models.CharField(max_length=50, default='pcs')
    images = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        app_label = 'shop'
        managed = False

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def profit_margin(self):
        if self.cost_price and self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return None


class Customer(UUIDModel):
    """B2B customers with credit tracking."""
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'
        app_label = 'shop'
        managed = False

    def __str__(self):
        return self.name

    @property
    def has_credit_available(self):
        return self.balance < self.credit_limit


class Supplier(UUIDModel):
    """Suppliers for purchase orders."""
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suppliers'
        app_label = 'shop'
        managed = False

    def __str__(self):
        return self.name


class Sale(UUIDModel):
    """Point-of-sale transaction."""

    STATUSES = [('completed', 'Completed'), ('voided', 'Voided')]
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('tigopesa', 'Tigo Pesa'),
        ('airtelmoney', 'Airtel Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Customer Credit'),
        ('pi', 'Pi Network'),
    ]

    sale_number = models.CharField(max_length=50, unique=True)
    customer_id = models.UUIDField(null=True, blank=True)
    cashier_id = models.UUIDField()
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='completed')
    voided_by = models.UUIDField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales'
        app_label = 'shop'
        managed = False

    def __str__(self):
        return f"Sale #{self.sale_number} — {self.total}"


class SaleItem(UUIDModel):
    """Line items for a sale."""
    sale_id = models.UUIDField()
    product_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'sale_items'
        app_label = 'shop'
        managed = False


class StockMovement(UUIDModel):
    """
    Immutable record of every stock change.
    Covers: sale, purchase, adjustment, damage, return, count_correction.
    """
    MOVEMENT_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('adjustment', 'Manual Adjustment'),
        ('damage', 'Damage/Loss'),
        ('return', 'Customer Return'),
        ('count_correction', 'Stock Count Correction'),
    ]

    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_before = models.IntegerField()
    quantity_change = models.IntegerField()  # negative = reduction
    quantity_after = models.IntegerField()
    reference_id = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.UUIDField()
    performed_by_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        app_label = 'shop'
        managed = False


class PurchaseOrder(UUIDModel):
    """Order from supplier to restock inventory."""

    STATUSES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('received', 'Fully Received'),
        ('partial', 'Partially Received'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='draft')
    total = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.UUIDField()
    approved_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'purchase_orders'
        app_label = 'shop'
        managed = False


class PurchaseOrderItem(UUIDModel):
    order_id = models.UUIDField()
    product_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=255)
    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'purchase_order_items'
        app_label = 'shop'
        managed = False


class Order(UUIDModel):
    """Wholesale order to a customer (B2B)."""

    STATUSES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('delivered', 'Delivered'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    customer_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='draft')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        app_label = 'shop'
        managed = False


class OrderItem(UUIDModel):
    order_id = models.UUIDField()
    product_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        app_label = 'shop'
        managed = False


class EmployeeApplication(UUIDModel):
    """
    HR onboarding: invited applicants fill a structured form.
    Collects personal info, documents (CV, ID, certificates).
    Approved applications → BusinessMember record in public schema.
    """

    STATUSES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    DISABILITY_STATUSES = [
        ('none', 'None'),
        ('visual', 'Visual'),
        ('hearing', 'Hearing'),
        ('physical', 'Physical'),
        ('other', 'Other'),
    ]

    invite_token = models.CharField(max_length=255, unique=True)
    invited_by = models.UUIDField()
    applicant_email = models.EmailField(max_length=255)
    applicant_name = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=100, blank=True)
    role_to_assign = models.CharField(max_length=20, blank=True)
    custom_permissions = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')

    # Personal details (filled by applicant)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    disability_status = models.CharField(
        max_length=50, choices=DISABILITY_STATUSES, default='none'
    )
    disability_details = models.TextField(blank=True)

    # Documents (Cloudinary URLs)
    passport_photo_url = models.URLField(max_length=500, blank=True)
    cv_url = models.URLField(max_length=500, blank=True)
    national_id_url = models.URLField(max_length=500, blank=True)
    certificates_urls = models.JSONField(default=list)

    # Background
    work_experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    languages_spoken = models.TextField(blank=True)
    digital_signature_url = models.URLField(max_length=500, blank=True)

    # HR review
    hr_notes = models.TextField(blank=True)
    reviewed_by = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'employee_applications'
        app_label = 'shop'
        managed = False


class TenantAuditLog(UUIDModel):
    """
    Immutable audit log per tenant schema.
    Protected by PostgreSQL trigger — no UPDATE/DELETE allowed.
    """
    user_id = models.UUIDField()
    user_name = models.CharField(max_length=255)
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_audit_log'
        app_label = 'shop'
        managed = False


class StockCount(UUIDModel):
    """Periodic stock count session."""
    tenant_id = models.UUIDField()
    counted_by = models.UUIDField(null=True, blank=True)
    count_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[('in_progress', 'In Progress'), ('completed', 'Completed')],
        default='in_progress'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'stock_counts'
        app_label = 'shop'
        managed = False


class StockCountItem(UUIDModel):
    stock_count_id = models.UUIDField()
    product_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=255)
    system_quantity = models.IntegerField()
    actual_quantity = models.IntegerField(null=True, blank=True)
    variance = models.IntegerField(null=True, blank=True)
    variance_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_count_items'
        app_label = 'shop'
        managed = False
