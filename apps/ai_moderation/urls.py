from django.urls import path
from . import views

urlpatterns = [
    path('queue/', views.moderation_queue, name='moderation-queue'),
    path('review/<uuid:listing_id>/', views.manual_review, name='manual-review'),
    path('remoderate/<uuid:listing_id>/', views.remoderate_listing, name='remoderate'),
]
