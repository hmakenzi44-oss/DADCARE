from django.urls import path
from . import views

urlpatterns = [
    # Auth (2-step: password → TOTP)
    path('auth/login/', views.sa_login_step1, name='sa-login'),
    path('auth/verify-totp/', views.sa_login_step2, name='sa-verify-totp'),
    path('auth/logout/', views.sa_logout, name='sa-logout'),
    path('auth/setup-totp/', views.setup_totp, name='sa-setup-totp'),
    path('auth/confirm-totp/', views.confirm_totp, name='sa-confirm-totp'),

    # Dashboard
    path('dashboard/', views.sa_dashboard, name='sa-dashboard'),

    # Tenant management
    path('tenants/', views.list_tenants, name='sa-tenants'),
    path('tenants/<uuid:tenant_id>/', views.tenant_detail, name='sa-tenant-detail'),
    path('tenants/<uuid:tenant_id>/update/', views.update_tenant, name='sa-tenant-update'),
    path('tenants/<uuid:tenant_id>/suspend/', views.suspend_tenant, name='sa-tenant-suspend'),
    path('tenants/<uuid:tenant_id>/reactivate/', views.reactivate_tenant, name='sa-tenant-reactivate'),

    # Subscription payments
    path('payments/', views.list_payments, name='sa-payments'),
    path('payments/<uuid:payment_id>/confirm/', views.confirm_payment, name='sa-payment-confirm'),
    path('payments/<uuid:payment_id>/reject/', views.reject_payment, name='sa-payment-reject'),

    # Mini-app feature flags
    path('mini-apps/', views.list_mini_apps, name='sa-mini-apps'),
    path('mini-apps/<uuid:app_id>/', views.update_mini_app, name='sa-mini-app-update'),

    # Marketplace moderation
    path('moderation/', views.sa_moderation_queue, name='sa-moderation'),
    path('moderation/<uuid:listing_id>/review/', views.sa_review_listing, name='sa-review'),

    # Audit log (immutable)
    path('audit/', views.audit_log, name='sa-audit'),

    # Users
    path('users/', views.list_users, name='sa-users'),
    path('users/<uuid:user_id>/toggle/', views.toggle_user, name='sa-user-toggle'),
]
