"""
Modèles pour la gestion des paiements de GourmetGuide.
Support Stripe et paiements mobiles africains (Tmoney, Flooz).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Payment(models.Model):
    """
    Modèle principal pour les paiements.
    """
    PAYMENT_METHOD_CHOICES = [
        ('stripe_card', _('Carte bancaire (Stripe)')),
        ('stripe_paypal', _('PayPal')),
        ('tmoney', _('Tmoney')),
        ('flooz', _('Flooz')),
        ('cash_on_delivery', _('Paiement à la livraison')),
        ('wallet', _('Portefeuille GourmetGuide')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Complété')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
        ('refunded', _('Remboursé')),
        ('partially_refunded', _('Partiellement remboursé')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(_('ID de transaction'), max_length=100, unique=True)
    
    # Relations
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Informations de paiement
    payment_method = models.CharField(_('Méthode de paiement'), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(
        _('Montant'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(_('Devise'), max_length=3, default='XOF')
    
    # Statut
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations externes (Stripe, etc.)
    external_payment_id = models.CharField(_('ID paiement externe'), max_length=200, blank=True)
    external_customer_id = models.CharField(_('ID client externe'), max_length=200, blank=True)
    
    # Métadonnées de la transaction
    payment_metadata = models.JSONField(
        _('Métadonnées de paiement'),
        default=dict,
        blank=True
    )
    
    # Informations de remboursement
    refund_amount = models.DecimalField(
        _('Montant remboursé'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    refund_reason = models.TextField(_('Raison du remboursement'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Complété le'), blank=True, null=True)
    failed_at = models.DateTimeField(_('Échoué le'), blank=True, null=True)
    
    # Messages d'erreur
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Paiement {self.transaction_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Génère un ID de transaction unique."""
        import random
        import string
        from django.utils import timezone
        
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"PAY{timestamp}{random_part}"
    
    def can_be_refunded(self):
        """Vérifie si le paiement peut être remboursé."""
        return self.status == 'completed' and self.refund_amount < self.amount


class PaymentMethod(models.Model):
    """
    Méthodes de paiement sauvegardées par les utilisateurs.
    """
    METHOD_TYPE_CHOICES = [
        ('stripe_card', _('Carte bancaire')),
        ('tmoney', _('Tmoney')),
        ('flooz', _('Flooz')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    # Type et nom
    method_type = models.CharField(_('Type de méthode'), max_length=20, choices=METHOD_TYPE_CHOICES)
    display_name = models.CharField(_('Nom d\'affichage'), max_length=100)
    
    # Informations de la méthode (cryptées ou tokenisées)
    external_id = models.CharField(_('ID externe'), max_length=200, blank=True)
    last_four_digits = models.CharField(_('4 derniers chiffres'), max_length=4, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(
        _('Métadonnées'),
        default=dict,
        blank=True
    )
    
    # Statut
    is_default = models.BooleanField(_('Méthode par défaut'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)
    
    # Expiration (pour les cartes)
    expires_at = models.DateField(_('Expire le'), blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Méthode de paiement')
        verbose_name_plural = _('Méthodes de paiement')
        ordering = ['-is_default', '-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.display_name}"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule méthode par défaut par utilisateur
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Wallet(models.Model):
    """
    Portefeuille virtuel GourmetGuide pour les utilisateurs.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Solde
    balance = models.DecimalField(
        _('Solde'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(_('Devise'), max_length=3, default='XOF')
    
    # Limites
    daily_limit = models.DecimalField(
        _('Limite quotidienne'),
        max_digits=8,
        decimal_places=2,
        default=1000.00
    )
    monthly_limit = models.DecimalField(
        _('Limite mensuelle'),
        max_digits=10,
        decimal_places=2,
        default=10000.00
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    is_frozen = models.BooleanField(_('Gelé'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Portefeuille')
        verbose_name_plural = _('Portefeuilles')
        
    def __str__(self):
        return f"Portefeuille de {self.user.email} - {self.balance} {self.currency}"
    
    def can_debit(self, amount):
        """Vérifie si le montant peut être débité."""
        return self.is_active and not self.is_frozen and self.balance >= amount
    
    def add_funds(self, amount, description=""):
        """Ajoute des fonds au portefeuille."""
        if amount > 0:
            self.balance += amount
            self.save()
            
            # Créer une transaction
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='credit',
                amount=amount,
                description=description or f"Ajout de fonds: {amount} {self.currency}"
            )
    
    def debit_funds(self, amount, description=""):
        """Débite des fonds du portefeuille."""
        if self.can_debit(amount):
            self.balance -= amount
            self.save()
            
            # Créer une transaction
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='debit',
                amount=amount,
                description=description or f"Débit: {amount} {self.currency}"
            )
            return True
        return False


class WalletTransaction(models.Model):
    """
    Historique des transactions du portefeuille.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('credit', _('Crédit')),
        ('debit', _('Débit')),
        ('refund', _('Remboursement')),
        ('bonus', _('Bonus')),
        ('penalty', _('Pénalité')),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Détails de la transaction
    transaction_type = models.CharField(_('Type de transaction'), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(
        _('Montant'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(_('Description'))
    
    # Solde après transaction
    balance_after = models.DecimalField(
        _('Solde après transaction'),
        max_digits=10,
        decimal_places=2
    )
    
    # Référence externe
    reference_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    reference_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Transaction de portefeuille')
        verbose_name_plural = _('Transactions de portefeuilles')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.wallet.currency}"
    
    def save(self, *args, **kwargs):
        if not self.balance_after:
            self.balance_after = self.wallet.balance
        super().save(*args, **kwargs)


class MobilePaymentProvider(models.Model):
    """
    Configuration des fournisseurs de paiement mobile.
    """
    PROVIDER_CHOICES = [
        ('tmoney', 'Tmoney'),
        ('flooz', 'Flooz'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('orange_money', 'Orange Money'),
    ]
    
    name = models.CharField(_('Nom'), max_length=50, choices=PROVIDER_CHOICES, unique=True)
    display_name = models.CharField(_('Nom d\'affichage'), max_length=100)
    logo = models.CharField(_('Logo'), max_length=255, blank=True)
    
    # Configuration API
    api_endpoint = models.URLField(_('Endpoint API'))
    api_key = models.CharField(_('Clé API'), max_length=200, blank=True)
    api_secret = models.CharField(_('Secret API'), max_length=200, blank=True)
    
    # Paramètres
    min_amount = models.DecimalField(
        _('Montant minimum'),
        max_digits=8,
        decimal_places=2,
        default=1.00
    )
    max_amount = models.DecimalField(
        _('Montant maximum'),
        max_digits=10,
        decimal_places=2,
        default=1000000.00
    )
    
    # Frais
    fixed_fee = models.DecimalField(
        _('Frais fixes'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    percentage_fee = models.DecimalField(
        _('Frais en pourcentage'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Pays supportés
    supported_countries = models.ManyToManyField(
        'core.Country',
        verbose_name=_('Pays supportés'),
        related_name='payment_providers'
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    is_test_mode = models.BooleanField(_('Mode test'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Fournisseur de paiement mobile')
        verbose_name_plural = _('Fournisseurs de paiement mobile')
        ordering = ['display_name']
        
    def __str__(self):
        return self.display_name
    
    def calculate_fee(self, amount):
        """Calcule les frais pour un montant donné."""
        percentage_amount = (amount * self.percentage_fee) / 100
        return self.fixed_fee + percentage_amount


class MobilePaymentTransaction(models.Model):
    """
    Transactions de paiement mobile spécifiques.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='mobile_transaction'
    )
    provider = models.ForeignKey(
        MobilePaymentProvider,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Informations du client mobile
    phone_number = models.CharField(_('Numéro de téléphone'), max_length=20)
    customer_name = models.CharField(_('Nom du client'), max_length=100, blank=True)
    
    # Informations de la transaction
    provider_transaction_id = models.CharField(_('ID transaction fournisseur'), max_length=200, blank=True)
    provider_reference = models.CharField(_('Référence fournisseur'), max_length=200, blank=True)
    
    # Réponse du fournisseur
    provider_response = models.JSONField(
        _('Réponse du fournisseur'),
        default=dict,
        blank=True
    )
    
    # Statut spécifique au mobile
    is_callback_received = models.BooleanField(_('Callback reçu'), default=False)
    callback_data = models.JSONField(
        _('Données de callback'),
        default=dict,
        blank=True
    )
    
    # Métadonnées
    initiated_at = models.DateTimeField(_('Initié le'), auto_now_add=True)
    callback_received_at = models.DateTimeField(_('Callback reçu le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Transaction de paiement mobile')
        verbose_name_plural = _('Transactions de paiement mobile')
        ordering = ['-initiated_at']
        
    def __str__(self):
        return f"{self.provider.display_name} - {self.phone_number}"


class Refund(models.Model):
    """
    Remboursements de paiements.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Complété')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
    ]
    
    REASON_CHOICES = [
        ('customer_request', _('Demande du client')),
        ('order_cancelled', _('Commande annulée')),
        ('delivery_failed', _('Échec de livraison')),
        ('quality_issue', _('Problème de qualité')),
        ('duplicate_payment', _('Paiement en double')),
        ('technical_error', _('Erreur technique')),
        ('other', _('Autre')),
    ]
    
    # Relations
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_refunds'
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds',
        limit_choices_to={'user_type': 'admin'}
    )
    
    # Détails du remboursement
    amount = models.DecimalField(
        _('Montant à rembourser'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    reason = models.CharField(_('Raison'), max_length=30, choices=REASON_CHOICES)
    description = models.TextField(_('Description'), blank=True)
    
    # Statut
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations externes
    external_refund_id = models.CharField(_('ID remboursement externe'), max_length=200, blank=True)
    
    # Métadonnées
    requested_at = models.DateTimeField(_('Demandé le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Complété le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Remboursement')
        verbose_name_plural = _('Remboursements')
        ordering = ['-requested_at']
        
    def __str__(self):
        return f"Remboursement {self.amount} {self.payment.currency} - {self.payment.transaction_id}"


class PaymentWebhook(models.Model):
    """
    Webhooks reçus des fournisseurs de paiement.
    """
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('tmoney', 'Tmoney'),
        ('flooz', 'Flooz'),
    ]
    
    STATUS_CHOICES = [
        ('received', _('Reçu')),
        ('processing', _('En cours de traitement')),
        ('processed', _('Traité')),
        ('failed', _('Échoué')),
        ('ignored', _('Ignoré')),
    ]
    
    # Fournisseur
    provider = models.CharField(_('Fournisseur'), max_length=20, choices=PROVIDER_CHOICES)
    
    # Données du webhook
    event_type = models.CharField(_('Type d\'événement'), max_length=100)
    event_id = models.CharField(_('ID d\'événement'), max_length=200, unique=True)
    
    # Payload
    payload = models.JSONField(_('Payload'))
    headers = models.JSONField(_('Headers'), default=dict, blank=True)
    
    # Traitement
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='received')
    processing_attempts = models.PositiveIntegerField(_('Tentatives de traitement'), default=0)
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    
    # Paiement associé
    related_payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks'
    )
    
    # Métadonnées
    received_at = models.DateTimeField(_('Reçu le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Webhook de paiement')
        verbose_name_plural = _('Webhooks de paiements')
        ordering = ['-received_at']
        
    def __str__(self):
        return f"{self.provider} - {self.event_type} ({self.event_id})"
