from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='auth-register'),
    path('login/', views.login, name='auth-login'),
    path('logout/', views.logout, name='auth-logout'),
    path('select-business/', views.select_business, name='auth-select-business'),
    path('profile/', views.profile, name='auth-profile'),
    path('profile/update/', views.update_profile, name='auth-update-profile'),
    path('change-password/', views.change_password, name='auth-change-password'),
]
