"""
Vues pour l'application notifications.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification, NotificationPreference


class NotificationListView(LoginRequiredMixin, ListView):
    """Liste des notifications."""
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une notification."""
    model = Notification
    template_name = 'notifications/detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Marquer comme lue
        if not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Marquer une notification comme lue."""
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('notifications:list')


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Marquer toutes les notifications comme lues."""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, _('Toutes les notifications ont été marquées comme lues'))
        return redirect('notifications:list')


class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    """Préférences de notifications."""
    model = NotificationPreference
    template_name = 'notifications/preferences.html'
    fields = ['email_notifications', 'sms_notifications', 'push_notifications']
    
    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notification_list(request):
    """API liste des notifications."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    data = []
    
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at,
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_unread_count(request):
    """API nombre de notifications non lues."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'count': count}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_read(request):
    """API marquer comme lu."""
    notification_id = request.data.get('notification_id')
    if notification_id:
        try:
            notification = Notification.objects.get(pk=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({'error': 'notification_id required'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_notification_preferences(request):
    """API préférences de notifications."""
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        data = {
            'email_notifications': preferences.email_notifications,
            'sms_notifications': preferences.sms_notifications,
            'push_notifications': preferences.push_notifications,
        }
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        # Mise à jour des préférences
        for field in ['email_notifications', 'sms_notifications', 'push_notifications']:
            if field in request.data:
                setattr(preferences, field, request.data[field])
        preferences.save()
        
        return Response({'message': 'Preferences updated'}, status=status.HTTP_200_OK)
