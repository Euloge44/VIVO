"""
URLs pour l'application delivery.
"""

from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    # Tableau de bord livreur
    path('dashboard/', views.DeliveryDashboardView.as_view(), name='dashboard'),
    path('available/', views.AvailableDeliveriesView.as_view(), name='available'),
    path('accept/<uuid:order_id>/', views.AcceptDeliveryView.as_view(), name='accept'),
    path('tracking/<uuid:order_id>/', views.DeliveryTrackingView.as_view(), name='tracking'),
    
    # API endpoints
    path('api/available/', views.api_available_deliveries, name='api_available'),
    path('api/accept/', views.api_accept_delivery, name='api_accept'),
    path('api/update-location/', views.api_update_location, name='api_update_location'),
    path('api/complete/', views.api_complete_delivery, name='api_complete'),
]