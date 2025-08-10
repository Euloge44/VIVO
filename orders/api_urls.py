"""
URLs pour l'API REST de l'application orders.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OrderViewSet, CartViewSet, CouponViewSet

# Créer le router pour les ViewSets
router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet)

app_name = 'orders_api'

urlpatterns = [
    # ViewSets via le router
    path('', include(router.urls)),
    
    # Endpoints spécialisés pour le panier
    path('cart/add/', CartViewSet.as_view({'post': 'add_item'}), name='cart_add'),
    path('cart/update/', CartViewSet.as_view({'put': 'update_item'}), name='cart_update'),
    path('cart/remove/', CartViewSet.as_view({'delete': 'remove_item'}), name='cart_remove'),
    path('cart/clear/', CartViewSet.as_view({'delete': 'clear'}), name='cart_clear'),
    path('cart/checkout/', CartViewSet.as_view({'post': 'checkout'}), name='cart_checkout'),
    
    # Validation de coupons
    path('coupons/validate/', CouponViewSet.as_view({'post': 'validate_coupon'}), name='validate_coupon'),
]