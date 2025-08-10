"""
Vues pour l'application delivery.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import DeliveryPerson, DeliveryAssignment


class DeliveryDashboardView(LoginRequiredMixin, View):
    """Tableau de bord livreur."""
    def get(self, request):
        try:
            delivery_person = DeliveryPerson.objects.get(user=request.user)
            context = {
                'delivery_person': delivery_person,
                'available_deliveries': [],  # À implémenter
                'today_earnings': 0,  # À implémenter
            }
            return render(request, 'delivery/dashboard.html', context)
        except DeliveryPerson.DoesNotExist:
            messages.error(request, _('Profil livreur non trouvé'))
            return redirect('accounts:profile')


class AvailableDeliveriesView(LoginRequiredMixin, ListView):
    """Livraisons disponibles."""
    template_name = 'delivery/available.html'
    context_object_name = 'deliveries'
    
    def get_queryset(self):
        # À implémenter avec les commandes disponibles
        return []


class AcceptDeliveryView(LoginRequiredMixin, View):
    """Accepter une livraison."""
    def post(self, request, order_id):
        # Logique d'acceptation à implémenter
        messages.success(request, _('Livraison acceptée'))
        return redirect('delivery:dashboard')


class DeliveryTrackingView(LoginRequiredMixin, View):
    """Suivi d'une livraison."""
    def get(self, request, order_id):
        # À implémenter
        return render(request, 'delivery/tracking.html', {'order_id': order_id})


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_available_deliveries(request):
    """API livraisons disponibles."""
    # À implémenter
    return Response([], status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_accept_delivery(request):
    """API accepter une livraison."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_update_location(request):
    """API mise à jour de la position."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_complete_delivery(request):
    """API finaliser une livraison."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
