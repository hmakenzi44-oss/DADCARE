from django.urls import path
from . import views

urlpatterns = [
    # Public (no auth)
    path('', views.browse_marketplace, name='marketplace-browse'),
    path('categories/', views.marketplace_categories, name='marketplace-categories'),
    path('<uuid:listing_id>/', views.listing_detail, name='marketplace-detail'),

    # Tenant (require_business)
    path('listings/submit/', views.submit_listing, name='listing-submit'),
    path('listings/mine/', views.my_listings, name='listing-mine'),
    path('listings/<uuid:listing_id>/update/', views.update_listing, name='listing-update'),
    path('listings/<uuid:listing_id>/delete/', views.delete_listing, name='listing-delete'),
]
