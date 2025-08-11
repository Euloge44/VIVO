"""
Vues pour l'application payments.
Gestion des paiements Stripe, mobiles et portefeuille.
"""

import json
import stripe
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, View, FormView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Payment, Wallet, WalletTransaction
from .forms import PaymentForm, WalletTopUpForm, MobilePaymentForm
from .utils import (
    PaymentProcessor, MobilePaymentSimulator, WalletManager,
    calculate_payment_fees, validate_payment_amount, 
    get_available_payment_methods, generate_payment_reference
)
from orders.models import Order


class ProcessPaymentView(LoginRequiredMixin, TemplateView):
    """Vue pour traiter un paiement."""
    template_name = 'payments/process.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la commande
        order_id = self.request.GET.get('order_id')
        if order_id:
            order = get_object_or_404(Order, id=order_id, user=self.request.user)
            context['order'] = order
            context['amount'] = order.total_amount
        else:
            # Récupération depuis la session (panier)
            amount = self.request.session.get('payment_amount')
            if amount:
                context['amount'] = Decimal(str(amount))
        
        # Méthodes de paiement disponibles
        context['payment_methods'] = get_available_payment_methods(
            user=self.request.user,
            amount=context.get('amount')
        )
        
        # Configuration Stripe
        context['STRIPE_PUBLISHABLE_KEY'] = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', '')
        
        return context


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Vue de succès de paiement."""
    template_name = 'payments/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les détails du paiement depuis la session
        payment_details = self.request.session.get('payment_success_details')
        if payment_details:
            context.update(payment_details)
            # Nettoyer la session
            del self.request.session['payment_success_details']
        
        return context


class PaymentCancelView(LoginRequiredMixin, TemplateView):
    """Vue d'annulation de paiement."""
    template_name = 'payments/cancel.html'


class WalletView(LoginRequiredMixin, TemplateView):
    """Vue du portefeuille utilisateur."""
    template_name = 'payments/wallet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Informations du portefeuille
        wallet, created = Wallet.objects.get_or_create(
            user=self.request.user,
            defaults={'balance': Decimal('0.00')}
        )
        
        context['wallet'] = wallet
        context['balance'] = wallet.balance
        
        # Transactions récentes
        context['recent_transactions'] = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:10]
        
        # Formulaire de rechargement
        context['top_up_form'] = WalletTopUpForm()
        
        return context


class WalletTopUpView(LoginRequiredMixin, FormView):
    """Vue pour recharger le portefeuille."""
    form_class = WalletTopUpForm
    template_name = 'payments/wallet_topup.html'
    success_url = reverse_lazy('payments:wallet')
    
    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        payment_method = form.cleaned_data['payment_method']
        
        # Valider le montant
        is_valid, error_msg = validate_payment_amount(amount, payment_method)
        if not is_valid:
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
        
        # Calculer les frais
        fees = calculate_payment_fees(amount, payment_method)
        total_amount = amount + fees
        
        # Traiter selon la méthode de paiement
        if payment_method == 'stripe':
            return self._process_stripe_topup(amount, total_amount)
        elif payment_method in ['tmoney', 'flooz']:
            return self._process_mobile_topup(payment_method, amount, total_amount)
        else:
            messages.error(self.request, _("Méthode de paiement non supportée"))
            return self.form_invalid(form)
    
    def _process_stripe_topup(self, amount: Decimal, total_amount: Decimal):
        """Traite un rechargement via Stripe."""
        result = PaymentProcessor.create_payment_intent(
            amount=total_amount,
            user_id=self.request.user.id
        )
        
        if result['success']:
            # Stocker les détails dans la session
            self.request.session['topup_details'] = {
                'amount': float(amount),
                'total_amount': float(total_amount),
                'payment_intent_id': result['payment_intent_id']
            }
            
            # Rediriger vers la page de paiement Stripe
            return redirect('payments:stripe_checkout')
        else:
            messages.error(self.request, f"Erreur Stripe: {result['error']}")
            return self.form_invalid(self.get_form())
    
    def _process_mobile_topup(self, provider: str, amount: Decimal, total_amount: Decimal):
        """Traite un rechargement via paiement mobile."""
        phone = self.request.user.phone
        
        if not phone:
            messages.error(self.request, _("Numéro de téléphone requis"))
            return self.form_invalid(self.get_form())
        
        result = MobilePaymentSimulator.initiate_payment(
            provider=provider,
            phone=phone,
            amount=total_amount
        )
        
        if result['success']:
            # Stocker les détails dans la session
            self.request.session['mobile_payment_details'] = {
                'transaction_id': result['transaction_id'],
                'provider': provider,
                'amount': float(amount),
                'total_amount': float(total_amount),
                'is_topup': True
            }
            
            messages.success(self.request, result['message'])
            return redirect('payments:mobile_payment_status')
        else:
            messages.error(self.request, result['error'])
            return self.form_invalid(self.get_form())


class MobilePaymentStatusView(LoginRequiredMixin, TemplateView):
    """Vue de statut des paiements mobiles."""
    template_name = 'payments/mobile_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les détails depuis la session
        payment_details = self.request.session.get('mobile_payment_details')
        if payment_details:
            context.update(payment_details)
        
        return context


# Webhooks et API

@csrf_exempt
def stripe_webhook(request):
    """Webhook pour les événements Stripe."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Traiter les événements
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        _handle_payment_success(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        _handle_payment_failure(payment_intent)
    
    return HttpResponse(status=200)


def _handle_payment_success(payment_intent):
    """Traite un paiement Stripe réussi."""
    try:
        order_id = payment_intent.metadata.get('order_id')
        user_id = payment_intent.metadata.get('user_id')
        amount = Decimal(str(payment_intent.amount_received / 100))
        
        # Créer l'enregistrement de paiement
        payment = Payment.objects.create(
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            payment_method='stripe',
            stripe_payment_intent_id=payment_intent.id,
            status='completed',
            reference=generate_payment_reference()
        )
        
        # Mettre à jour la commande si applicable
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'paid'
                order.save()
            except Order.DoesNotExist:
                pass
        
        print(f"Paiement Stripe réussi: {payment.reference}")
        
    except Exception as e:
        print(f"Erreur lors du traitement du paiement Stripe: {e}")


def _handle_payment_failure(payment_intent):
    """Traite un échec de paiement Stripe."""
    try:
        order_id = payment_intent.metadata.get('order_id')
        user_id = payment_intent.metadata.get('user_id')
        
        # Créer l'enregistrement de paiement échoué
        Payment.objects.create(
            user_id=user_id,
            order_id=order_id,
            amount=Decimal(str(payment_intent.amount / 100)),
            payment_method='stripe',
            stripe_payment_intent_id=payment_intent.id,
            status='failed',
            reference=generate_payment_reference()
        )
        
        print(f"Paiement Stripe échoué pour commande: {order_id}")
        
    except Exception as e:
        print(f"Erreur lors du traitement de l'échec Stripe: {e}")


# API Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_payment_intent(request):
    """API pour créer un PaymentIntent Stripe."""
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
        order_id = request.data.get('order_id')
        
        # Valider le montant
        is_valid, error_msg = validate_payment_amount(amount, 'stripe')
        if not is_valid:
            return Response({
                'success': False,
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le PaymentIntent
        result = PaymentProcessor.create_payment_intent(
            amount=amount,
            order_id=order_id,
            user_id=request.user.id
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_initiate_mobile_payment(request):
    """API pour initier un paiement mobile."""
    try:
        provider = request.data.get('provider')
        phone = request.data.get('phone') or request.user.phone
        amount = Decimal(str(request.data.get('amount', 0)))
        order_id = request.data.get('order_id')
        
        if not phone:
            return Response({
                'success': False,
                'error': 'Numéro de téléphone requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider le montant
        is_valid, error_msg = validate_payment_amount(amount, provider)
        if not is_valid:
            return Response({
                'success': False,
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initier le paiement
        result = MobilePaymentSimulator.initiate_payment(
            provider=provider,
            phone=phone,
            amount=amount,
            order_id=order_id
        )
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_check_mobile_payment(request, transaction_id):
    """API pour vérifier le statut d'un paiement mobile."""
    try:
        result = MobilePaymentSimulator.check_payment_status(transaction_id)
        
        # Si le paiement est complété, traiter la commande
        if result.get('success') and result.get('status') == 'completed':
            _process_mobile_payment_completion(transaction_id, request.user)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wallet_payment(request):
    """API pour payer avec le portefeuille."""
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
        order_id = request.data.get('order_id')
        description = request.data.get('description', 'Paiement commande')
        
        # Valider le montant
        is_valid, error_msg = validate_payment_amount(amount, 'wallet')
        if not is_valid:
            return Response({
                'success': False,
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Effectuer le paiement
        result = WalletManager.deduct_funds(
            user_id=request.user.id,
            amount=amount,
            transaction_type='payment',
            description=description
        )
        
        if result['success']:
            # Créer l'enregistrement de paiement
            payment = Payment.objects.create(
                user=request.user,
                order_id=order_id,
                amount=amount,
                payment_method='wallet',
                status='completed',
                reference=generate_payment_reference()
            )
            
            # Mettre à jour la commande
            if order_id:
                try:
                    order = Order.objects.get(id=order_id, user=request.user)
                    order.payment_status = 'paid'
                    order.save()
                except Order.DoesNotExist:
                    pass
            
            result['payment_reference'] = payment.reference
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_wallet_balance(request):
    """API pour obtenir le solde du portefeuille."""
    try:
        balance = WalletManager.get_balance(request.user.id)
        
        return Response({
            'success': True,
            'balance': float(balance),
            'formatted_balance': f"{balance} FCFA"
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_wallet_topup(request):
    """API pour recharger le portefeuille."""
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
        payment_method = request.data.get('payment_method')
        
        # Valider le montant
        is_valid, error_msg = validate_payment_amount(amount, payment_method)
        if not is_valid:
            return Response({
                'success': False,
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculer les frais
        fees = calculate_payment_fees(amount, payment_method)
        total_amount = amount + fees
        
        if payment_method == 'stripe':
            # Créer un PaymentIntent pour le rechargement
            result = PaymentProcessor.create_payment_intent(
                amount=total_amount,
                user_id=request.user.id
            )
            
            if result['success']:
                result['topup_amount'] = float(amount)
                result['fees'] = float(fees)
            
            return Response(result)
            
        elif payment_method in ['tmoney', 'flooz']:
            # Initier le paiement mobile
            phone = request.data.get('phone') or request.user.phone
            
            if not phone:
                return Response({
                    'success': False,
                    'error': 'Numéro de téléphone requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = MobilePaymentSimulator.initiate_payment(
                provider=payment_method,
                phone=phone,
                amount=total_amount
            )
            
            if result['success']:
                result['topup_amount'] = float(amount)
            
            return Response(result)
        
        else:
            return Response({
                'success': False,
                'error': 'Méthode de paiement non supportée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_payment_methods(request):
    """API pour obtenir les méthodes de paiement disponibles."""
    try:
        amount = request.GET.get('amount')
        if amount:
            amount = Decimal(str(amount))
        
        methods = get_available_payment_methods(
            user=request.user,
            amount=amount
        )
        
        return Response({
            'success': True,
            'payment_methods': methods
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_payment_history(request):
    """API pour l'historique des paiements."""
    try:
        payments = Payment.objects.filter(user=request.user).order_by('-created_at')
        
        payment_data = []
        for payment in payments:
            payment_data.append({
                'id': str(payment.id),
                'reference': payment.reference,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'status': payment.status,
                'created_at': payment.created_at.isoformat(),
                'order_id': str(payment.order_id) if payment.order else None
            })
        
        return Response({
            'success': True,
            'payments': payment_data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Fonctions utilitaires

def _process_mobile_payment_completion(transaction_id: str, user):
    """Traite la completion d'un paiement mobile."""
    from django.core.cache import cache
    
    payment_data = cache.get(f'mobile_payment_{transaction_id}')
    if not payment_data:
        return
    
    try:
        amount = Decimal(str(payment_data['amount']))
        
        # Créer l'enregistrement de paiement
        payment = Payment.objects.create(
            user=user,
            order_id=payment_data.get('order_id'),
            amount=amount,
            payment_method=payment_data['provider'],
            mobile_transaction_id=transaction_id,
            status='completed',
            reference=generate_payment_reference()
        )
        
        # Si c'est un rechargement de portefeuille
        if payment_data.get('is_topup'):
            WalletManager.add_funds(
                user_id=user.id,
                amount=amount,
                transaction_type='mobile_topup',
                description=f'Rechargement via {payment_data["provider"]}'
            )
        
        # Mettre à jour la commande si applicable
        order_id = payment_data.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=user)
                order.payment_status = 'paid'
                order.save()
            except Order.DoesNotExist:
                pass
        
        print(f"Paiement mobile complété: {payment.reference}")
        
    except Exception as e:
        print(f"Erreur lors du traitement du paiement mobile: {e}")


# Vues pour simuler les paiements (développement uniquement)

@login_required
def simulate_mobile_payment(request, transaction_id):
    """Simule la completion d'un paiement mobile (dev uniquement)."""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Non disponible en production'}, status=403)
    
    success = request.GET.get('success', 'true').lower() == 'true'
    
    result = MobilePaymentSimulator.simulate_payment_completion(
        transaction_id=transaction_id,
        success=success
    )
    
    if result['success'] and result['status'] == 'completed':
        _process_mobile_payment_completion(transaction_id, request.user)
    
    return JsonResponse(result)
