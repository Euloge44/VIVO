"""
URLs pour l'API REST de l'application accounts.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserViewSet, UserProfileViewSet, UserDeviceViewSet

# Créer le router pour les ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)
router.register(r'devices', UserDeviceViewSet)

app_name = 'accounts_api'

urlpatterns = [
    # ViewSets via le router
    path('', include(router.urls)),
    
    # Endpoints d'authentification directs (pour compatibilité)
    path('auth/login/', UserViewSet.as_view({'post': 'login'}), name='auth_login'),
    path('auth/register/', UserViewSet.as_view({'post': 'register'}), name='auth_register'),
    path('auth/logout/', UserViewSet.as_view({'post': 'logout'}), name='auth_logout'),
    path('auth/profile/', UserViewSet.as_view({'get': 'profile', 'put': 'update_profile'}), name='auth_profile'),
    path('auth/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='change_password'),
    path('auth/stats/', UserViewSet.as_view({'get': 'stats'}), name='user_stats'),
]