"""
URLs pour l'application analytics.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Tableaux de bord analytics
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('restaurant/<int:restaurant_id>/', views.RestaurantAnalyticsView.as_view(), name='restaurant'),
    path('sales/', views.SalesAnalyticsView.as_view(), name='sales'),
    path('users/', views.UserAnalyticsView.as_view(), name='users'),
    
    # API endpoints
    path('api/dashboard/', views.api_dashboard_stats, name='api_dashboard'),
    path('api/sales/', views.api_sales_data, name='api_sales'),
    path('api/popular-items/', views.api_popular_items, name='api_popular_items'),
    path('api/user-behavior/', views.api_user_behavior, name='api_user_behavior'),
]