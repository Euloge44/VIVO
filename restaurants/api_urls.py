"""
URLs pour l'API REST de l'application restaurants.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RestaurantViewSet, MenuItemViewSet, CategoryViewSet, SpecialOfferViewSet

# Créer le router pour les ViewSets
router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'menu-items', MenuItemViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'offers', SpecialOfferViewSet)

app_name = 'restaurants_api'

urlpatterns = [
    # ViewSets via le router
    path('', include(router.urls)),
    
    # Endpoints spécialisés
    path('search/', RestaurantViewSet.as_view({'post': 'search'}), name='restaurant_search'),
]