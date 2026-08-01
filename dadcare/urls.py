from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Tenant-facing API (dadcare.app / shop.dadcare.app)
    path('api/auth/', include('apps.auth_app.urls')),
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/shop/', include('apps.shop.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
    path('api/ai/', include('apps.ai_moderation.urls')),

    # Super Admin panel (control.dadcare.app)
    # In production: Nginx routes control.dadcare.app/sa/* here
    path('sa/', include('apps.super_admin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# SPA catch-all — serves base.html for all frontend routes
from django.views.generic import TemplateView
spa_view = TemplateView.as_view(template_name='base.html')
urlpatterns += [
    path('', spa_view),
    path('shop/', spa_view),
    path('marketplace/', spa_view),
]
