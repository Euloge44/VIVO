"""
Modèles pour le système de fidélité de GourmetGuide.
Cartes de fidélité virtuelles avec points et récompenses.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class LoyaltyCard(models.Model):
    """
    Cartes de fidélité virtuelles des clients.
    """
    TIER_CHOICES = [
        ('bronze', _('Bronze')),
        ('silver', _('Argent')),
        ('gold', _('Or')),
        ('platinum', _('Platine')),
        ('diamond', _('Diamant')),
    ]
    
    # Relations
    customer = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='loyalty_card',
        limit_choices_to={'user_type': 'client'}
    )
    
    # Identifiants
    card_number = models.CharField(_('Numéro de carte'), max_length=20, unique=True)
    qr_code = models.CharField(_('Code QR'), max_length=100, unique=True)
    
    # Points et niveau
    total_points = models.PositiveIntegerField(_('Points totaux'), default=0)
    available_points = models.PositiveIntegerField(_('Points disponibles'), default=0)
    used_points = models.PositiveIntegerField(_('Points utilisés'), default=0)
    tier = models.CharField(_('Niveau'), max_length=20, choices=TIER_CHOICES, default='bronze')
    
    # Statistiques
    total_orders = models.PositiveIntegerField(_('Commandes totales'), default=0)
    total_spent = models.DecimalField(
        _('Montant total dépensé'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_activity = models.DateTimeField(_('Dernière activité'), auto_now=True)
    
    class Meta:
        verbose_name = _('Carte de fidélité')
        verbose_name_plural = _('Cartes de fidélité')
        
    def __str__(self):
        return f"Carte {self.card_number} - {self.customer.email} ({self.get_tier_display()})"
    
    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self.generate_card_number()
        if not self.qr_code:
            self.qr_code = self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_card_number(self):
        """Génère un numéro de carte unique."""
        import random
        
        while True:
            number = f"GG{''.join([str(random.randint(0, 9)) for _ in range(12)])}"
            if not LoyaltyCard.objects.filter(card_number=number).exists():
                return number
    
    def generate_qr_code(self):
        """Génère un code QR unique."""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            if not LoyaltyCard.objects.filter(qr_code=code).exists():
                return code
    
    def add_points(self, points, description=""):
        """Ajoute des points à la carte."""
        if points > 0:
            self.total_points += points
            self.available_points += points
            self.update_tier()
            self.save()
            
            # Enregistrer la transaction
            PointTransaction.objects.create(
                loyalty_card=self,
                transaction_type='earned',
                points=points,
                description=description or f"Points gagnés: {points}"
            )
    
    def use_points(self, points, description=""):
        """Utilise des points de la carte."""
        if points > 0 and self.available_points >= points:
            self.available_points -= points
            self.used_points += points
            self.save()
            
            # Enregistrer la transaction
            PointTransaction.objects.create(
                loyalty_card=self,
                transaction_type='redeemed',
                points=points,
                description=description or f"Points utilisés: {points}"
            )
            return True
        return False
    
    def update_tier(self):
        """Met à jour le niveau de fidélité basé sur les points totaux."""
        if self.total_points >= 10000:
            self.tier = 'diamond'
        elif self.total_points >= 5000:
            self.tier = 'platinum'
        elif self.total_points >= 2000:
            self.tier = 'gold'
        elif self.total_points >= 500:
            self.tier = 'silver'
        else:
            self.tier = 'bronze'
    
    def get_tier_benefits(self):
        """Retourne les avantages du niveau actuel."""
        benefits = {
            'bronze': {'discount': 0, 'free_delivery_threshold': 50},
            'silver': {'discount': 5, 'free_delivery_threshold': 40},
            'gold': {'discount': 10, 'free_delivery_threshold': 30},
            'platinum': {'discount': 15, 'free_delivery_threshold': 20},
            'diamond': {'discount': 20, 'free_delivery_threshold': 10},
        }
        return benefits.get(self.tier, benefits['bronze'])


class PointTransaction(models.Model):
    """
    Historique des transactions de points de fidélité.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('earned', _('Gagnés')),
        ('redeemed', _('Utilisés')),
        ('expired', _('Expirés')),
        ('bonus', _('Bonus')),
        ('penalty', _('Pénalité')),
        ('refund', _('Remboursement')),
    ]
    
    loyalty_card = models.ForeignKey(
        LoyaltyCard,
        on_delete=models.CASCADE,
        related_name='point_transactions'
    )
    
    # Détails de la transaction
    transaction_type = models.CharField(_('Type de transaction'), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField(_('Points'))
    description = models.TextField(_('Description'))
    
    # Points après transaction
    balance_after = models.PositiveIntegerField(_('Solde après transaction'))
    
    # Références
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_transactions'
    )
    related_reward = models.ForeignKey(
        'LoyaltyReward',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='point_transactions'
    )
    
    # Expiration (pour les points gagnés)
    expires_at = models.DateTimeField(_('Expire le'), blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Transaction de points')
        verbose_name_plural = _('Transactions de points')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.points} points - {self.loyalty_card.customer.email}"


class LoyaltyReward(models.Model):
    """
    Récompenses disponibles avec les points de fidélité.
    """
    REWARD_TYPE_CHOICES = [
        ('discount_percentage', _('Remise en pourcentage')),
        ('discount_fixed', _('Remise fixe')),
        ('free_delivery', _('Livraison gratuite')),
        ('free_item', _('Plat gratuit')),
        ('upgrade', _('Surclassement')),
        ('gift', _('Cadeau')),
    ]
    
    # Informations de base
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    image = models.CharField(_('Image'), max_length=255, blank=True)
    
    # Type et valeur
    reward_type = models.CharField(_('Type de récompense'), max_length=20, choices=REWARD_TYPE_CHOICES)
    reward_value = models.DecimalField(
        _('Valeur de la récompense'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    
    # Coût en points
    points_required = models.PositiveIntegerField(_('Points requis'))
    
    # Conditions
    min_order_amount = models.DecimalField(
        _('Montant minimum de commande'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    tier_required = models.CharField(
        _('Niveau requis'),
        max_length=20,
        choices=LoyaltyCard.TIER_CHOICES,
        blank=True
    )
    
    # Restaurants applicables
    applicable_restaurants = models.ManyToManyField(
        'restaurants.Restaurant',
        verbose_name=_('Restaurants applicables'),
        blank=True,
        related_name='loyalty_rewards'
    )
    
    # Éléments de menu applicables (pour les plats gratuits)
    applicable_menu_items = models.ManyToManyField(
        'restaurants.MenuItem',
        verbose_name=_('Plats applicables'),
        blank=True,
        related_name='loyalty_rewards'
    )
    
    # Limitations
    max_redemptions = models.PositiveIntegerField(_('Rachats maximum'), blank=True, null=True)
    max_redemptions_per_user = models.PositiveIntegerField(_('Rachats par utilisateur'), default=1)
    current_redemptions = models.PositiveIntegerField(_('Rachats actuels'), default=0)
    
    # Période de validité
    start_date = models.DateTimeField(_('Date de début'), blank=True, null=True)
    end_date = models.DateTimeField(_('Date de fin'), blank=True, null=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    is_featured = models.BooleanField(_('Récompense vedette'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Récompense de fidélité')
        verbose_name_plural = _('Récompenses de fidélité')
        ordering = ['-is_featured', 'points_required']
        
    def __str__(self):
        return f"{self.title} ({self.points_required} points)"
    
    def can_be_redeemed_by(self, loyalty_card):
        """Vérifie si la récompense peut être rachetée par une carte."""
        from django.utils import timezone
        
        # Vérifier les points
        if loyalty_card.available_points < self.points_required:
            return False, _("Points insuffisants.")
        
        # Vérifier le niveau
        if self.tier_required:
            tier_order = ['bronze', 'silver', 'gold', 'platinum', 'diamond']
            required_index = tier_order.index(self.tier_required)
            current_index = tier_order.index(loyalty_card.tier)
            if current_index < required_index:
                return False, _("Niveau de fidélité insuffisant.")
        
        # Vérifier la période
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False, _("Cette récompense n'est pas encore disponible.")
        if self.end_date and now > self.end_date:
            return False, _("Cette récompense a expiré.")
        
        # Vérifier les limitations globales
        if self.max_redemptions and self.current_redemptions >= self.max_redemptions:
            return False, _("Cette récompense n'est plus disponible.")
        
        # Vérifier les limitations par utilisateur
        user_redemptions = RewardRedemption.objects.filter(
            reward=self,
            loyalty_card=loyalty_card
        ).count()
        if user_redemptions >= self.max_redemptions_per_user:
            return False, _("Vous avez déjà utilisé cette récompense le maximum de fois autorisé.")
        
        return True, _("Récompense disponible.")


class RewardRedemption(models.Model):
    """
    Historique des rachats de récompenses.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('used', _('Utilisé')),
        ('expired', _('Expiré')),
        ('cancelled', _('Annulé')),
    ]
    
    # Relations
    loyalty_card = models.ForeignKey(
        LoyaltyCard,
        on_delete=models.CASCADE,
        related_name='reward_redemptions'
    )
    reward = models.ForeignKey(
        LoyaltyReward,
        on_delete=models.CASCADE,
        related_name='redemptions'
    )
    
    # Code de rachat unique
    redemption_code = models.CharField(_('Code de rachat'), max_length=20, unique=True)
    
    # Points utilisés
    points_used = models.PositiveIntegerField(_('Points utilisés'))
    
    # Utilisation
    order_used_in = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_redemptions'
    )
    
    # Statut et validité
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField(_('Expire le'))
    
    # Métadonnées
    redeemed_at = models.DateTimeField(_('Racheté le'), auto_now_add=True)
    used_at = models.DateTimeField(_('Utilisé le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Rachat de récompense')
        verbose_name_plural = _('Rachats de récompenses')
        ordering = ['-redeemed_at']
        
    def __str__(self):
        return f"Rachat {self.redemption_code} - {self.reward.title}"
    
    def save(self, *args, **kwargs):
        if not self.redemption_code:
            self.redemption_code = self.generate_redemption_code()
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def generate_redemption_code(self):
        """Génère un code de rachat unique."""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not RewardRedemption.objects.filter(redemption_code=code).exists():
                return code
    
    def is_valid(self):
        """Vérifie si le rachat est encore valide."""
        from django.utils import timezone
        return (
            self.status in ['approved', 'pending'] and
            timezone.now() < self.expires_at
        )


class LoyaltyProgram(models.Model):
    """
    Programmes de fidélité spécifiques aux restaurants.
    """
    restaurant = models.OneToOneField(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='loyalty_program'
    )
    
    # Configuration du programme
    name = models.CharField(_('Nom du programme'), max_length=200)
    description = models.TextField(_('Description'))
    
    # Règles de points
    points_per_euro = models.PositiveIntegerField(_('Points par euro'), default=10)
    bonus_multiplier = models.DecimalField(
        _('Multiplicateur de bonus'),
        max_digits=3,
        decimal_places=1,
        default=1.0
    )
    
    # Seuils de niveau
    silver_threshold = models.PositiveIntegerField(_('Seuil Argent'), default=500)
    gold_threshold = models.PositiveIntegerField(_('Seuil Or'), default=2000)
    platinum_threshold = models.PositiveIntegerField(_('Seuil Platine'), default=5000)
    diamond_threshold = models.PositiveIntegerField(_('Seuil Diamant'), default=10000)
    
    # Avantages par niveau
    tier_benefits = models.JSONField(
        _('Avantages par niveau'),
        default=dict,
        help_text=_('Configuration des avantages pour chaque niveau')
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Programme de fidélité')
        verbose_name_plural = _('Programmes de fidélité')
        
    def __str__(self):
        return f"Programme {self.name} - {self.restaurant.name}"


class LoyaltyEvent(models.Model):
    """
    Événements spéciaux de fidélité (double points, etc.).
    """
    EVENT_TYPE_CHOICES = [
        ('double_points', _('Double points')),
        ('triple_points', _('Triple points')),
        ('bonus_points', _('Points bonus')),
        ('free_delivery', _('Livraison gratuite')),
        ('special_discount', _('Remise spéciale')),
    ]
    
    # Informations de base
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    event_type = models.CharField(_('Type d\'événement'), max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # Configuration
    multiplier = models.DecimalField(
        _('Multiplicateur'),
        max_digits=3,
        decimal_places=1,
        default=2.0
    )
    bonus_points = models.PositiveIntegerField(_('Points bonus'), default=0)
    discount_percentage = models.DecimalField(
        _('Pourcentage de remise'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Conditions
    min_order_amount = models.DecimalField(
        _('Montant minimum'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    tier_required = models.CharField(
        _('Niveau requis'),
        max_length=20,
        choices=LoyaltyCard.TIER_CHOICES,
        blank=True
    )
    
    # Restaurants participants
    participating_restaurants = models.ManyToManyField(
        'restaurants.Restaurant',
        verbose_name=_('Restaurants participants'),
        blank=True,
        related_name='loyalty_events'
    )
    
    # Période
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'))
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Événement de fidélité')
        verbose_name_plural = _('Événements de fidélité')
        ordering = ['-start_date']
        
    def __str__(self):
        return self.title
    
    def is_active_now(self):
        """Vérifie si l'événement est actif maintenant."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )
    
    def applies_to_order(self, order):
        """Vérifie si l'événement s'applique à une commande."""
        if not self.is_active_now():
            return False
        
        # Vérifier le montant minimum
        if order.total_amount < self.min_order_amount:
            return False
        
        # Vérifier le niveau requis
        if self.tier_required:
            loyalty_card = getattr(order.customer, 'loyalty_card', None)
            if not loyalty_card or loyalty_card.tier != self.tier_required:
                return False
        
        # Vérifier le restaurant
        if self.participating_restaurants.exists():
            if not self.participating_restaurants.filter(id=order.restaurant.id).exists():
                return False
        
        return True


class ReferralProgram(models.Model):
    """
    Programme de parrainage.
    """
    # Récompenses
    referrer_points = models.PositiveIntegerField(_('Points pour le parrain'), default=100)
    referee_points = models.PositiveIntegerField(_('Points pour le filleul'), default=50)
    referrer_discount = models.DecimalField(
        _('Remise pour le parrain'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    referee_discount = models.DecimalField(
        _('Remise pour le filleul'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Conditions
    min_referee_order_amount = models.DecimalField(
        _('Montant minimum première commande filleul'),
        max_digits=8,
        decimal_places=2,
        default=20.00
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Programme de parrainage')
        verbose_name_plural = _('Programmes de parrainage')
        
    def __str__(self):
        return f"Programme de parrainage - {self.referrer_points}/{self.referee_points} points"


class Referral(models.Model):
    """
    Parrainages entre utilisateurs.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('completed', _('Complété')),
        ('expired', _('Expiré')),
        ('cancelled', _('Annulé')),
    ]
    
    # Relations
    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referrals_made',
        limit_choices_to={'user_type': 'client'}
    )
    referee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='referrals_received',
        limit_choices_to={'user_type': 'client'}
    )
    program = models.ForeignKey(
        ReferralProgram,
        on_delete=models.CASCADE,
        related_name='referrals'
    )
    
    # Code de parrainage
    referral_code = models.CharField(_('Code de parrainage'), max_length=20, unique=True)
    
    # Statut et validation
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completing_referrals'
    )
    
    # Récompenses accordées
    referrer_points_awarded = models.PositiveIntegerField(_('Points accordés au parrain'), default=0)
    referee_points_awarded = models.PositiveIntegerField(_('Points accordés au filleul'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Complété le'), blank=True, null=True)
    expires_at = models.DateTimeField(_('Expire le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Parrainage')
        verbose_name_plural = _('Parrainages')
        unique_together = ['referrer', 'referee']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Parrainage {self.referral_code}: {self.referrer.email} → {self.referee.email}"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        if not self.expires_at:
            from django.utils import timezone
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Génère un code de parrainage unique."""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Referral.objects.filter(referral_code=code).exists():
                return code
