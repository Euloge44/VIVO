"""
URLs pour l'application notifications.
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Gestion des notifications
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    
    # Préférences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    
    # API endpoints
    path('api/list/', views.api_notification_list, name='api_list'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/mark-read/', views.api_mark_read, name='api_mark_read'),
    path('api/preferences/', views.api_notification_preferences, name='api_preferences'),
]