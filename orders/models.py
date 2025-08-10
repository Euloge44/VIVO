"""
Modèles pour la gestion des commandes de GourmetGuide.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


class Order(models.Model):
    """
    Modèle principal pour les commandes.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmée')),
        ('preparing', _('En préparation')),
        ('ready', _('Prête')),
        ('picked_up', _('Récupérée par le livreur')),
        ('delivering', _('En livraison')),
        ('delivered', _('Livrée')),
        ('cancelled', _('Annulée')),
        ('refunded', _('Remboursée')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Complété')),
        ('failed', _('Échoué')),
        ('refunded', _('Remboursé')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_('Numéro de commande'), max_length=20, unique=True)
    
    # Relations
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'user_type': 'client'}
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    delivery_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders',
        limit_choices_to={'user_type': 'delivery'}
    )
    
    # Statuts
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(_('Statut du paiement'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Informations de livraison
    delivery_address = models.TextField(_('Adresse de livraison'))
    delivery_latitude = models.DecimalField(
        _('Latitude de livraison'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    delivery_longitude = models.DecimalField(
        _('Longitude de livraison'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    delivery_instructions = models.TextField(_('Instructions de livraison'), blank=True)
    
    # Montants
    subtotal = models.DecimalField(
        _('Sous-total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    delivery_fee = models.DecimalField(
        _('Frais de livraison'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        _('Montant des taxes'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        _('Montant de la remise'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        _('Montant total'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Offre spéciale appliquée
    applied_offer = models.ForeignKey(
        'restaurants.SpecialOffer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_in_orders'
    )
    
    # Temps
    estimated_delivery_time = models.DateTimeField(_('Heure de livraison estimée'), blank=True, null=True)
    actual_delivery_time = models.DateTimeField(_('Heure de livraison réelle'), blank=True, null=True)
    
    # Notes
    customer_notes = models.TextField(_('Notes du client'), blank=True)
    restaurant_notes = models.TextField(_('Notes du restaurant'), blank=True)
    delivery_notes = models.TextField(_('Notes du livreur'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Commande {self.order_number} - {self.customer.email}"
    
    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Génère un numéro de commande unique."""
        import random
        import string
        from django.utils import timezone
        
        timestamp = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"GG{timestamp}{random_part}"
    
    def calculate_total(self):
        """Calcule le montant total de la commande."""
        self.subtotal = sum(item.get_total_price() for item in self.items.all())
        self.total_amount = self.subtotal + self.delivery_fee + self.tax_amount - self.discount_amount
        return self.total_amount
    
    def can_be_cancelled(self):
        """Vérifie si la commande peut être annulée."""
        return self.status in ['pending', 'confirmed']
    
    def can_be_rated(self):
        """Vérifie si la commande peut être évaluée."""
        return self.status == 'delivered'


class OrderItem(models.Model):
    """
    Éléments individuels d'une commande.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        'restaurants.MenuItem',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    
    # Quantité et prix
    quantity = models.PositiveIntegerField(_('Quantité'), validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        _('Prix unitaire'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Personnalisations
    customizations = models.JSONField(
        _('Personnalisations'),
        default=dict,
        blank=True,
        help_text=_('Personnalisations choisies par le client')
    )
    special_instructions = models.TextField(_('Instructions spéciales'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Élément de commande')
        verbose_name_plural = _('Éléments de commandes')
        
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - Commande {self.order.order_number}"
    
    def get_total_price(self):
        """Calcule le prix total pour cet élément."""
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.menu_item.get_discounted_price()
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Historique des changements de statut des commandes.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    previous_status = models.CharField(_('Statut précédent'), max_length=20, blank=True)
    new_status = models.CharField(_('Nouveau statut'), max_length=20)
    
    # Qui a effectué le changement
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes'
    )
    
    # Notes sur le changement
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    timestamp = models.DateTimeField(_('Horodatage'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historique de statut')
        verbose_name_plural = _('Historiques de statuts')
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Commande {self.order.order_number}: {self.previous_status} → {self.new_status}"


class Cart(models.Model):
    """
    Panier temporaire pour les clients.
    """
    customer = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        limit_choices_to={'user_type': 'client'}
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Panier')
        verbose_name_plural = _('Paniers')
        
    def __str__(self):
        return f"Panier de {self.customer.email}"
    
    def get_total_items(self):
        """Retourne le nombre total d'éléments dans le panier."""
        return sum(item.quantity for item in self.items.all())
    
    def get_subtotal(self):
        """Calcule le sous-total du panier."""
        return sum(item.get_total_price() for item in self.items.all())
    
    def clear(self):
        """Vide le panier."""
        self.items.all().delete()
        self.restaurant = None
        self.save()


class CartItem(models.Model):
    """
    Éléments dans le panier d'un client.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        'restaurants.MenuItem',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    
    # Quantité et personnalisations
    quantity = models.PositiveIntegerField(_('Quantité'), validators=[MinValueValidator(1)])
    customizations = models.JSONField(
        _('Personnalisations'),
        default=dict,
        blank=True
    )
    special_instructions = models.TextField(_('Instructions spéciales'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Élément du panier')
        verbose_name_plural = _('Éléments du panier')
        unique_together = ['cart', 'menu_item']
        
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    def get_unit_price(self):
        """Retourne le prix unitaire avec les personnalisations."""
        base_price = self.menu_item.get_discounted_price()
        # Ajouter les coûts de personnalisation si nécessaire
        return base_price
    
    def get_total_price(self):
        """Calcule le prix total pour cet élément."""
        return self.quantity * self.get_unit_price()


class OrderTracking(models.Model):
    """
    Suivi en temps réel des commandes.
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='tracking'
    )
    
    # Localisation actuelle du livreur
    current_latitude = models.DecimalField(
        _('Latitude actuelle'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    current_longitude = models.DecimalField(
        _('Longitude actuelle'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Estimations
    estimated_preparation_time = models.PositiveIntegerField(_('Temps de préparation estimé (minutes)'), default=30)
    estimated_delivery_time = models.PositiveIntegerField(_('Temps de livraison estimé (minutes)'), default=30)
    
    # Temps réels
    preparation_started_at = models.DateTimeField(_('Préparation commencée à'), blank=True, null=True)
    preparation_completed_at = models.DateTimeField(_('Préparation terminée à'), blank=True, null=True)
    pickup_time = models.DateTimeField(_('Heure de récupération'), blank=True, null=True)
    delivery_started_at = models.DateTimeField(_('Livraison commencée à'), blank=True, null=True)
    delivered_at = models.DateTimeField(_('Livrée à'), blank=True, null=True)
    
    # Distance et itinéraire
    distance_to_customer = models.DecimalField(
        _('Distance jusqu\'au client (km)'),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Dernière mise à jour
    last_updated = models.DateTimeField(_('Dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('Suivi de commande')
        verbose_name_plural = _('Suivis de commandes')
        
    def __str__(self):
        return f"Suivi - Commande {self.order.order_number}"
    
    def get_total_delivery_time(self):
        """Calcule le temps total de livraison."""
        if self.delivered_at and self.order.created_at:
            return (self.delivered_at - self.order.created_at).total_seconds() / 60
        return None


class Coupon(models.Model):
    """
    Coupons de réduction pour les commandes.
    """
    COUPON_TYPE_CHOICES = [
        ('percentage', _('Pourcentage')),
        ('fixed_amount', _('Montant fixe')),
        ('free_delivery', _('Livraison gratuite')),
    ]
    
    # Informations de base
    code = models.CharField(_('Code'), max_length=50, unique=True)
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Type et valeur
    coupon_type = models.CharField(_('Type'), max_length=20, choices=COUPON_TYPE_CHOICES)
    discount_value = models.DecimalField(
        _('Valeur de la remise'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Conditions d'utilisation
    min_order_amount = models.DecimalField(
        _('Montant minimum'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    max_discount_amount = models.DecimalField(
        _('Remise maximum'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Limitations
    max_uses = models.PositiveIntegerField(_('Utilisations maximum'), blank=True, null=True)
    max_uses_per_user = models.PositiveIntegerField(_('Utilisations par utilisateur'), default=1)
    current_uses = models.PositiveIntegerField(_('Utilisations actuelles'), default=0)
    
    # Restaurants applicables
    applicable_restaurants = models.ManyToManyField(
        'restaurants.Restaurant',
        verbose_name=_('Restaurants applicables'),
        blank=True,
        related_name='applicable_coupons'
    )
    
    # Période de validité
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'))
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def is_valid_for_order(self, order_amount, restaurant=None, user=None):
        """Vérifie si le coupon est valide pour une commande."""
        from django.utils import timezone
        
        now = timezone.now()
        
        # Vérifier la période de validité
        if not (self.start_date <= now <= self.end_date):
            return False, _("Ce coupon n'est plus valide.")
        
        # Vérifier le statut
        if not self.is_active:
            return False, _("Ce coupon n'est pas actif.")
        
        # Vérifier le montant minimum
        if order_amount < self.min_order_amount:
            return False, _("Le montant minimum de commande n'est pas atteint.")
        
        # Vérifier les utilisations globales
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, _("Ce coupon a atteint sa limite d'utilisation.")
        
        # Vérifier le restaurant
        if restaurant and self.applicable_restaurants.exists():
            if not self.applicable_restaurants.filter(id=restaurant.id).exists():
                return False, _("Ce coupon n'est pas valide pour ce restaurant.")
        
        # Vérifier les utilisations par utilisateur
        if user:
            user_uses = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_uses >= self.max_uses_per_user:
                return False, _("Vous avez déjà utilisé ce coupon le maximum de fois autorisé.")
        
        return True, _("Coupon valide.")
    
    def calculate_discount(self, order_amount):
        """Calcule le montant de la remise."""
        if self.coupon_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        elif self.coupon_type == 'fixed_amount':
            return min(self.discount_value, order_amount)
        elif self.coupon_type == 'free_delivery':
            return 0  # La livraison gratuite est gérée séparément
        return 0


class CouponUsage(models.Model):
    """
    Historique d'utilisation des coupons.
    """
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usage_history'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coupon_usage'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='coupon_usage'
    )
    
    discount_amount = models.DecimalField(
        _('Montant de la remise'),
        max_digits=8,
        decimal_places=2
    )
    
    used_at = models.DateTimeField(_('Utilisé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Utilisation de coupon')
        verbose_name_plural = _('Utilisations de coupons')
        unique_together = ['coupon', 'order']
        
    def __str__(self):
        return f"{self.coupon.code} utilisé par {self.user.email}"
