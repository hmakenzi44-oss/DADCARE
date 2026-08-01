from django.urls import path
from . import views

urlpatterns = [
    path('mini-apps/', views.list_mini_apps, name='mini-apps-list'),
    path('create/', views.create_business, name='business-create'),
    path('me/', views.business_detail, name='business-detail'),
    path('me/update/', views.update_business, name='business-update'),
    path('members/', views.list_members, name='members-list'),
    path('members/<uuid:member_id>/remove/', views.remove_member, name='member-remove'),
    path('members/<uuid:member_id>/permissions/', views.update_member_permissions, name='member-permissions'),
    path('invite/', views.create_invite, name='invite-create'),
    path('join/', views.join_business, name='business-join'),
]
