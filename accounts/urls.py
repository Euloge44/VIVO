"""
URLs pour l'application accounts.
Gestion de l'authentification multi-rôles.
"""

from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification web
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/choice/', views.register_choice_view, name='register_choice'),
    
    # Profil utilisateur
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),
    path('delete/', views.delete_account, name='delete_account'),
    
    # Tableaux de bord
    path('dashboard/client/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('dashboard/restaurant/', views.RestaurantDashboardView.as_view(), name='restaurant_dashboard'),
    path('dashboard/delivery/', views.DeliveryDashboardView.as_view(), name='delivery_dashboard'),
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Utilitaires
    path('switch-language/', views.switch_language, name='switch_language'),
    
    # API endpoints
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/stats/', views.api_user_stats, name='api_user_stats'),
    path('api/upload-avatar/', views.api_upload_avatar, name='api_upload_avatar'),
    
    # Intégration django-allauth (optionnel)
    path('allauth/', include('allauth.urls')),
]