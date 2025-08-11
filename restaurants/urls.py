"""
URLs pour l'application restaurants.
"""

from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    # Vues publiques
    path('', views.RestaurantListView.as_view(), name='list'),
    path('map/', views.RestaurantMapView.as_view(), name='map'),
    path('<int:pk>/', views.RestaurantDetailView.as_view(), name='detail'),
    path('<int:pk>/menu/', views.RestaurantMenuView.as_view(), name='menu'),
    
    # Tableau de bord restaurant
    path('dashboard/', views.RestaurantDashboardView.as_view(), name='dashboard'),
    path('dashboard/menu/', views.MenuManagementView.as_view(), name='menu_management'),
    path('dashboard/orders/', views.OrderManagementView.as_view(), name='order_management'),
    path('dashboard/stats/', views.RestaurantStatsView.as_view(), name='stats'),
    
    # API endpoints
    path('api/list/', views.api_restaurant_list, name='api_list'),
    path('api/<int:pk>/', views.api_restaurant_detail, name='api_detail'),
    path('api/<int:pk>/menu/', views.api_restaurant_menu, name='api_menu'),
    path('api/search/', views.api_restaurant_search, name='api_search'),
]