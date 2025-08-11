"""
URLs pour l'application orders.
"""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Gestion des commandes
    path('', views.OrderListView.as_view(), name='list'),
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('create/', views.OrderCreateView.as_view(), name='create'),
    path('<uuid:pk>/track/', views.OrderTrackingView.as_view(), name='track'),
    
    # Panier
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/', views.UpdateCartView.as_view(), name='update_cart'),
    path('cart/remove/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    
    # API endpoints
    path('api/list/', views.api_order_list, name='api_list'),
    path('api/<uuid:pk>/', views.api_order_detail, name='api_detail'),
    path('api/create/', views.api_order_create, name='api_create'),
    path('api/<uuid:pk>/status/', views.api_order_status, name='api_status'),
    path('api/cart/', views.api_cart, name='api_cart'),
]