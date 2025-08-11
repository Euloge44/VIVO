"""
Utilitaires de paiement pour GourmetGuide.
Support de Stripe et simulation des paiements mobiles africains (Tmoney, Flooz).
"""

import stripe
import json
import uuid
import hashlib
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


# Configuration Stripe
if hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentProcessor:
    """Classe principale pour traiter les paiements."""
    
    @staticmethod
    def create_payment_intent(amount: Decimal, currency: str = 'xof', 
                            order_id: str = None, user_id: int = None) -> Dict:
        """
        Crée un PaymentIntent Stripe.
        
        Args:
            amount: Montant en centimes
            currency: Devise (xof pour FCFA)
            order_id: ID de la commande
            user_id: ID de l'utilisateur
        
        Returns:
            Dictionnaire avec les détails du PaymentIntent
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe utilise les centimes
                currency=currency,
                metadata={
                    'order_id': order_id,
                    'user_id': str(user_id),
                    'platform': 'gourmetguide'
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': amount,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'general_error'
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id: str) -> Dict:
        """
        Confirme un paiement Stripe.
        
        Args:
            payment_intent_id: ID du PaymentIntent
        
        Returns:
            Statut de la confirmation
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': intent.status,
                'amount_received': intent.amount_received / 100,
                'metadata': intent.metadata
            }
            
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }


class MobilePaymentSimulator:
    """Simulateur pour les paiements mobiles africains."""
    
    PROVIDERS = {
        'tmoney': {
            'name': 'Tmoney',
            'country': 'TG',
            'currency': 'XOF',
            'min_amount': 100,
            'max_amount': 500000,
            'fees': 0.02  # 2%
        },
        'flooz': {
            'name': 'Flooz',
            'country': 'TG',
            'currency': 'XOF',
            'min_amount': 100,
            'max_amount': 300000,
            'fees': 0.015  # 1.5%
        }
    }
    
    @classmethod
    def initiate_payment(cls, provider: str, phone: str, amount: Decimal, 
                        order_id: str = None) -> Dict:
        """
        Initie un paiement mobile.
        
        Args:
            provider: Fournisseur (tmoney, flooz)
            phone: Numéro de téléphone
            amount: Montant en FCFA
            order_id: ID de la commande
        
        Returns:
            Résultat de l'initiation
        """
        if provider not in cls.PROVIDERS:
            return {
                'success': False,
                'error': f'Fournisseur non supporté: {provider}'
            }
        
        provider_info = cls.PROVIDERS[provider]
        
        # Validation du montant
        if amount < provider_info['min_amount'] or amount > provider_info['max_amount']:
            return {
                'success': False,
                'error': f'Montant invalide. Min: {provider_info["min_amount"]}, Max: {provider_info["max_amount"]}'
            }
        
        # Validation du téléphone
        if not cls._validate_phone(phone, provider_info['country']):
            return {
                'success': False,
                'error': 'Numéro de téléphone invalide'
            }
        
        # Générer un ID de transaction unique
        transaction_id = cls._generate_transaction_id(provider, phone, amount)
        
        # Calculer les frais
        fees = amount * Decimal(str(provider_info['fees']))
        total_amount = amount + fees
        
        # Simuler l'initiation du paiement
        payment_data = {
            'transaction_id': transaction_id,
            'provider': provider,
            'phone': phone,
            'amount': float(amount),
            'fees': float(fees),
            'total_amount': float(total_amount),
            'currency': provider_info['currency'],
            'status': 'pending',
            'order_id': order_id,
            'created_at': timezone.now().isoformat(),
            'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }
        
        # Stocker dans le cache pour 5 minutes
        cache.set(f'mobile_payment_{transaction_id}', payment_data, 300)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'provider_name': provider_info['name'],
            'amount': float(amount),
            'fees': float(fees),
            'total_amount': float(total_amount),
            'phone': phone,
            'message': f'Paiement initié. Composez *{cls._get_ussd_code(provider)}# pour confirmer.',
            'ussd_code': cls._get_ussd_code(provider),
            'expires_in': 300  # 5 minutes
        }
    
    @classmethod
    def check_payment_status(cls, transaction_id: str) -> Dict:
        """
        Vérifie le statut d'un paiement mobile.
        
        Args:
            transaction_id: ID de la transaction
        
        Returns:
            Statut du paiement
        """
        payment_data = cache.get(f'mobile_payment_{transaction_id}')
        
        if not payment_data:
            return {
                'success': False,
                'error': 'Transaction non trouvée ou expirée'
            }
        
        # Simuler différents statuts basés sur le temps
        created_at = timezone.datetime.fromisoformat(payment_data['created_at'].replace('Z', '+00:00'))
        elapsed = (timezone.now() - created_at).total_seconds()
        
        if elapsed < 30:
            status = 'pending'
        elif elapsed < 120:
            # 80% de chance de succès après 30 secondes
            import random
            status = 'completed' if random.random() < 0.8 else 'pending'
        elif elapsed < 180:
            # 95% de chance de succès après 2 minutes
            import random
            status = 'completed' if random.random() < 0.95 else 'failed'
        else:
            # Timeout après 3 minutes
            status = 'failed'
        
        payment_data['status'] = status
        
        if status == 'completed':
            payment_data['completed_at'] = timezone.now().isoformat()
        elif status == 'failed':
            payment_data['failed_at'] = timezone.now().isoformat()
            payment_data['error_message'] = 'Paiement échoué ou annulé par l\'utilisateur'
        
        # Mettre à jour le cache
        cache.set(f'mobile_payment_{transaction_id}', payment_data, 300)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': status,
            'amount': payment_data['amount'],
            'provider': payment_data['provider'],
            'message': cls._get_status_message(status),
            'completed_at': payment_data.get('completed_at'),
            'error_message': payment_data.get('error_message')
        }
    
    @classmethod
    def simulate_payment_completion(cls, transaction_id: str, success: bool = True) -> Dict:
        """
        Simule la completion d'un paiement (pour les tests).
        
        Args:
            transaction_id: ID de la transaction
            success: Si le paiement doit réussir
        
        Returns:
            Résultat de la simulation
        """
        payment_data = cache.get(f'mobile_payment_{transaction_id}')
        
        if not payment_data:
            return {
                'success': False,
                'error': 'Transaction non trouvée'
            }
        
        if success:
            payment_data['status'] = 'completed'
            payment_data['completed_at'] = timezone.now().isoformat()
        else:
            payment_data['status'] = 'failed'
            payment_data['failed_at'] = timezone.now().isoformat()
            payment_data['error_message'] = 'Paiement simulé comme échoué'
        
        cache.set(f'mobile_payment_{transaction_id}', payment_data, 300)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': payment_data['status'],
            'message': cls._get_status_message(payment_data['status'])
        }
    
    @staticmethod
    def _validate_phone(phone: str, country: str) -> bool:
        """Valide un numéro de téléphone selon le pays."""
        if country == 'TG':  # Togo
            # Format: +228 XX XX XX XX
            import re
            pattern = r'^\+228\s?[0-9]{8}$'
            return bool(re.match(pattern, phone.replace(' ', '')))
        return False
    
    @staticmethod
    def _generate_transaction_id(provider: str, phone: str, amount: Decimal) -> str:
        """Génère un ID de transaction unique."""
        data = f"{provider}_{phone}_{amount}_{timezone.now().timestamp()}"
        return hashlib.md5(data.encode()).hexdigest()[:16].upper()
    
    @staticmethod
    def _get_ussd_code(provider: str) -> str:
        """Retourne le code USSD pour un fournisseur."""
        codes = {
            'tmoney': '332',
            'flooz': '155'
        }
        return codes.get(provider, '000')
    
    @staticmethod
    def _get_status_message(status: str) -> str:
        """Retourne un message selon le statut."""
        messages = {
            'pending': 'Paiement en attente de confirmation',
            'completed': 'Paiement confirmé avec succès',
            'failed': 'Paiement échoué',
            'cancelled': 'Paiement annulé'
        }
        return messages.get(status, 'Statut inconnu')


class WalletManager:
    """Gestionnaire de portefeuille virtuel."""
    
    @staticmethod
    def get_balance(user_id: int) -> Decimal:
        """Obtient le solde du portefeuille d'un utilisateur."""
        from .models import Wallet
        
        try:
            wallet = Wallet.objects.get(user_id=user_id)
            return wallet.balance
        except Wallet.DoesNotExist:
            return Decimal('0.00')
    
    @staticmethod
    def add_funds(user_id: int, amount: Decimal, 
                  transaction_type: str = 'top_up',
                  description: str = None) -> Dict:
        """
        Ajoute des fonds au portefeuille.
        
        Args:
            user_id: ID de l'utilisateur
            amount: Montant à ajouter
            transaction_type: Type de transaction
            description: Description optionnelle
        
        Returns:
            Résultat de l'opération
        """
        from .models import Wallet, WalletTransaction
        
        try:
            wallet, created = Wallet.objects.get_or_create(
                user_id=user_id,
                defaults={'balance': Decimal('0.00')}
            )
            
            # Ajouter les fonds
            wallet.balance += amount
            wallet.save()
            
            # Enregistrer la transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount,
                description=description or f'Ajout de {amount} FCFA',
                balance_after=wallet.balance
            )
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'amount_added': amount
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def deduct_funds(user_id: int, amount: Decimal, 
                    transaction_type: str = 'payment',
                    description: str = None) -> Dict:
        """
        Déduit des fonds du portefeuille.
        
        Args:
            user_id: ID de l'utilisateur
            amount: Montant à déduire
            transaction_type: Type de transaction
            description: Description optionnelle
        
        Returns:
            Résultat de l'opération
        """
        from .models import Wallet, WalletTransaction
        
        try:
            wallet = Wallet.objects.get(user_id=user_id)
            
            if wallet.balance < amount:
                return {
                    'success': False,
                    'error': 'Solde insuffisant',
                    'current_balance': wallet.balance,
                    'required_amount': amount
                }
            
            # Déduire les fonds
            wallet.balance -= amount
            wallet.save()
            
            # Enregistrer la transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=transaction_type,
                amount=-amount,
                description=description or f'Paiement de {amount} FCFA',
                balance_after=wallet.balance
            )
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'amount_deducted': amount
            }
            
        except Wallet.DoesNotExist:
            return {
                'success': False,
                'error': 'Portefeuille non trouvé'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def transfer_funds(from_user_id: int, to_user_id: int, amount: Decimal,
                      description: str = None) -> Dict:
        """
        Transfère des fonds entre deux portefeuilles.
        
        Args:
            from_user_id: ID de l'expéditeur
            to_user_id: ID du destinataire
            amount: Montant à transférer
            description: Description du transfert
        
        Returns:
            Résultat du transfert
        """
        # Déduire du portefeuille expéditeur
        deduct_result = WalletManager.deduct_funds(
            from_user_id, amount, 'transfer_out',
            description or f'Transfert vers utilisateur {to_user_id}'
        )
        
        if not deduct_result['success']:
            return deduct_result
        
        # Ajouter au portefeuille destinataire
        add_result = WalletManager.add_funds(
            to_user_id, amount, 'transfer_in',
            description or f'Transfert de utilisateur {from_user_id}'
        )
        
        if not add_result['success']:
            # Annuler la déduction en cas d'échec
            WalletManager.add_funds(
                from_user_id, amount, 'refund',
                'Remboursement suite à échec de transfert'
            )
            return add_result
        
        return {
            'success': True,
            'amount_transferred': amount,
            'sender_balance': deduct_result['new_balance'],
            'recipient_balance': add_result['new_balance']
        }


def calculate_payment_fees(amount: Decimal, payment_method: str) -> Decimal:
    """
    Calcule les frais de paiement selon la méthode.
    
    Args:
        amount: Montant de base
        payment_method: Méthode de paiement
    
    Returns:
        Montant des frais
    """
    fees_config = {
        'stripe': Decimal('0.029'),  # 2.9% + 30 centimes
        'tmoney': Decimal('0.02'),   # 2%
        'flooz': Decimal('0.015'),   # 1.5%
        'wallet': Decimal('0.00'),   # Gratuit
        'cash': Decimal('0.00')      # Gratuit
    }
    
    fee_rate = fees_config.get(payment_method, Decimal('0.00'))
    
    if payment_method == 'stripe':
        # Stripe: 2.9% + 30 centimes
        return (amount * fee_rate) + Decimal('0.30')
    else:
        return amount * fee_rate


def generate_payment_reference() -> str:
    """Génère une référence de paiement unique."""
    return f"GG{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


def validate_payment_amount(amount: Decimal, payment_method: str) -> Tuple[bool, str]:
    """
    Valide un montant de paiement selon la méthode.
    
    Args:
        amount: Montant à valider
        payment_method: Méthode de paiement
    
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if amount <= 0:
        return False, "Le montant doit être positif"
    
    # Limites par méthode de paiement
    limits = {
        'stripe': {'min': Decimal('1.00'), 'max': Decimal('1000000.00')},
        'tmoney': {'min': Decimal('100.00'), 'max': Decimal('500000.00')},
        'flooz': {'min': Decimal('100.00'), 'max': Decimal('300000.00')},
        'wallet': {'min': Decimal('1.00'), 'max': Decimal('1000000.00')},
        'cash': {'min': Decimal('1.00'), 'max': Decimal('50000.00')}
    }
    
    if payment_method in limits:
        limit = limits[payment_method]
        if amount < limit['min']:
            return False, f"Montant minimum: {limit['min']} FCFA"
        if amount > limit['max']:
            return False, f"Montant maximum: {limit['max']} FCFA"
    
    return True, ""


def format_payment_method_name(method: str) -> str:
    """Formate le nom d'une méthode de paiement pour l'affichage."""
    names = {
        'stripe': 'Carte bancaire (Stripe)',
        'tmoney': 'Tmoney',
        'flooz': 'Flooz',
        'wallet': 'Portefeuille GourmetGuide',
        'cash': 'Paiement à la livraison'
    }
    return names.get(method, method.title())


def get_available_payment_methods(user=None, amount=None) -> List[Dict]:
    """
    Retourne la liste des méthodes de paiement disponibles.
    
    Args:
        user: Utilisateur (optionnel)
        amount: Montant (optionnel)
    
    Returns:
        Liste des méthodes disponibles
    """
    methods = [
        {
            'id': 'stripe',
            'name': 'Carte bancaire',
            'description': 'Visa, Mastercard, American Express',
            'icon': 'fas fa-credit-card',
            'fees': '2.9% + 30¢',
            'available': hasattr(settings, 'STRIPE_PUBLISHABLE_KEY')
        },
        {
            'id': 'tmoney',
            'name': 'Tmoney',
            'description': 'Paiement mobile Togocom',
            'icon': 'fas fa-mobile-alt',
            'fees': '2%',
            'available': True
        },
        {
            'id': 'flooz',
            'name': 'Flooz',
            'description': 'Paiement mobile Moov',
            'icon': 'fas fa-mobile-alt',
            'fees': '1.5%',
            'available': True
        },
        {
            'id': 'cash',
            'name': 'Espèces',
            'description': 'Paiement à la livraison',
            'icon': 'fas fa-money-bill-wave',
            'fees': 'Gratuit',
            'available': True
        }
    ]
    
    # Ajouter le portefeuille si l'utilisateur est connecté
    if user and user.is_authenticated:
        wallet_balance = WalletManager.get_balance(user.id)
        methods.insert(-1, {
            'id': 'wallet',
            'name': 'Portefeuille GourmetGuide',
            'description': f'Solde: {wallet_balance} FCFA',
            'icon': 'fas fa-wallet',
            'fees': 'Gratuit',
            'available': True,
            'balance': float(wallet_balance),
            'sufficient': amount is None or wallet_balance >= amount
        })
    
    return [method for method in methods if method['available']]


def create_stripe_checkout_session(order_id: str, amount: Decimal, 
                                 success_url: str, cancel_url: str) -> Dict:
    """
    Crée une session de checkout Stripe.
    
    Args:
        order_id: ID de la commande
        amount: Montant en FCFA
        success_url: URL de succès
        cancel_url: URL d'annulation
    
    Returns:
        Session de checkout
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'xof',
                    'product_data': {
                        'name': f'Commande GourmetGuide #{order_id}',
                        'description': 'Livraison de repas'
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'order_id': order_id,
                'platform': 'gourmetguide'
            }
        )
        
        return {
            'success': True,
            'session_id': session.id,
            'checkout_url': session.url
        }
        
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': str(e)
        }