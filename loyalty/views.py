"""
Vues pour l'application loyalty.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import LoyaltyCard, LoyaltyReward, PointTransaction


class LoyaltyDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord fidélité."""
    template_name = 'loyalty/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card, created = LoyaltyCard.objects.get_or_create(user=self.request.user)
        context['loyalty_card'] = card
        context['available_rewards'] = LoyaltyReward.objects.filter(is_active=True)
        return context


class LoyaltyCardView(LoginRequiredMixin, TemplateView):
    """Carte de fidélité."""
    template_name = 'loyalty/card.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        card, created = LoyaltyCard.objects.get_or_create(user=self.request.user)
        context['loyalty_card'] = card
        return context


class RewardsView(LoginRequiredMixin, ListView):
    """Liste des récompenses."""
    model = LoyaltyReward
    template_name = 'loyalty/rewards.html'
    context_object_name = 'rewards'
    
    def get_queryset(self):
        return LoyaltyReward.objects.filter(is_active=True)


class RedeemRewardView(LoginRequiredMixin, View):
    """Échanger une récompense."""
    def post(self, request, reward_id):
        # Logique d'échange à implémenter
        messages.success(request, _('Récompense échangée avec succès'))
        return redirect('loyalty:dashboard')


class PointHistoryView(LoginRequiredMixin, ListView):
    """Historique des points."""
    model = PointTransaction
    template_name = 'loyalty/history.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        card, created = LoyaltyCard.objects.get_or_create(user=self.request.user)
        return PointTransaction.objects.filter(loyalty_card=card).order_by('-created_at')


class ReferralProgramView(LoginRequiredMixin, TemplateView):
    """Programme de parrainage."""
    template_name = 'loyalty/referral.html'


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_loyalty_card(request):
    """API carte de fidélité."""
    card, created = LoyaltyCard.objects.get_or_create(user=request.user)
    data = {
        'card_number': card.card_number,
        'points_balance': card.points_balance,
        'tier': card.tier,
        'created_at': card.created_at,
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_points_balance(request):
    """API solde de points."""
    card, created = LoyaltyCard.objects.get_or_create(user=request.user)
    return Response({'points': card.points_balance}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_available_rewards(request):
    """API récompenses disponibles."""
    rewards = LoyaltyReward.objects.filter(is_active=True)
    data = []
    
    for reward in rewards:
        data.append({
            'id': reward.id,
            'name': reward.name,
            'description': reward.description,
            'points_required': reward.points_required,
            'value': float(reward.value) if reward.value else None,
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_redeem_reward(request):
    """API échanger une récompense."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_point_history(request):
    """API historique des points."""
    card, created = LoyaltyCard.objects.get_or_create(user=request.user)
    transactions = PointTransaction.objects.filter(loyalty_card=card).order_by('-created_at')[:50]
    
    data = []
    for transaction in transactions:
        data.append({
            'id': transaction.id,
            'transaction_type': transaction.transaction_type,
            'points': transaction.points,
            'description': transaction.description,
            'created_at': transaction.created_at,
        })
    
    return Response(data, status=status.HTTP_200_OK)
