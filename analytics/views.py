"""
Vues pour l'application analytics.
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import DailyStats, RestaurantStats


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord analytics."""
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Données analytics à implémenter
        context['stats'] = {
            'total_orders': 0,
            'total_revenue': 0,
            'active_users': 0,
            'growth_rate': 0,
        }
        return context


class RestaurantAnalyticsView(LoginRequiredMixin, TemplateView):
    """Analytics d'un restaurant."""
    template_name = 'analytics/restaurant.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant_id = kwargs.get('restaurant_id')
        # Données analytics du restaurant à implémenter
        context['restaurant_id'] = restaurant_id
        return context


class SalesAnalyticsView(LoginRequiredMixin, TemplateView):
    """Analytics des ventes."""
    template_name = 'analytics/sales.html'


class UserAnalyticsView(LoginRequiredMixin, TemplateView):
    """Analytics des utilisateurs."""
    template_name = 'analytics/users.html'


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_stats(request):
    """API statistiques du tableau de bord."""
    # À implémenter avec de vraies données
    data = {
        'total_orders': 0,
        'total_revenue': 0,
        'active_users': 0,
        'growth_rate': 0,
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_sales_data(request):
    """API données de ventes."""
    # À implémenter
    return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_popular_items(request):
    """API articles populaires."""
    # À implémenter
    return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_behavior(request):
    """API comportement utilisateur."""
    # À implémenter
    return Response({}, status=status.HTTP_200_OK)
