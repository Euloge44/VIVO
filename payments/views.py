"""
Vues pour l'application payments.
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, Wallet


class ProcessPaymentView(LoginRequiredMixin, View):
    """Traitement d'un paiement."""
    def post(self, request):
        # Logique de paiement à implémenter
        messages.success(request, _('Paiement traité avec succès'))
        return redirect('payments:success')


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Page de succès de paiement."""
    template_name = 'payments/success.html'


class PaymentCancelView(LoginRequiredMixin, TemplateView):
    """Page d'annulation de paiement."""
    template_name = 'payments/cancel.html'


class WalletView(LoginRequiredMixin, View):
    """Portefeuille utilisateur."""
    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        context = {
            'wallet': wallet,
            'transactions': [],  # À implémenter
        }
        return render(request, 'payments/wallet.html', context)


class WalletTopUpView(LoginRequiredMixin, View):
    """Recharge du portefeuille."""
    def post(self, request):
        # Logique de recharge à implémenter
        messages.success(request, _('Portefeuille rechargé'))
        return redirect('payments:wallet')


def stripe_webhook(request):
    """Webhook Stripe."""
    # À implémenter
    return HttpResponse(status=200)


# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_process_payment(request):
    """API traitement de paiement."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_payment_methods(request):
    """API méthodes de paiement."""
    # À implémenter
    return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wallet(request):
    """API portefeuille."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    data = {
        'balance': float(wallet.balance),
        'currency': 'XOF'
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mobile_payment(request):
    """API paiement mobile."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
