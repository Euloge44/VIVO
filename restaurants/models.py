"""
Modèles pour la gestion des restaurants, catégories et menus.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey

User = get_user_model()


class Category(MPTTModel):
    """
    Catégories de cuisine hiérarchiques (locale, internationale, etc.).
    """
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)
    icon = models.CharField(_('Icône'), max_length=50, blank=True, help_text=_('Classe CSS pour l\'icône'))
    image = models.CharField(_('Image'), max_length=255, blank=True)
    
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Catégorie parent')
    )
    
    # Métadonnées
    is_active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('restaurants:category', kwargs={'slug': self.slug})


class Restaurant(models.Model):
    """
    Modèle principal pour les restaurants.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente de validation')),
        ('active', _('Actif')),
        ('inactive', _('Inactif')),
        ('suspended', _('Suspendu')),
    ]
    
    # Informations de base
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_restaurants',
        limit_choices_to={'user_type': 'restaurant'}
    )
    name = models.CharField(_('Nom du restaurant'), max_length=200)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'))
    
    # Catégories
    categories = models.ManyToManyField(
        Category,
        verbose_name=_('Catégories'),
        related_name='restaurants'
    )
    
    # Images
    logo = models.CharField(_('Logo'), max_length=255, blank=True)
    cover_image = models.CharField(_('Image de couverture'), max_length=255, blank=True)
    
    # Informations de contact
    phone = models.CharField(_('Téléphone'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    website = models.URLField(_('Site web'), blank=True)
    
    # Adresse et géolocalisation
    address = models.TextField(_('Adresse'))
    city = models.CharField(_('Ville'), max_length=100)
    postal_code = models.CharField(_('Code postal'), max_length=10)
    country = models.CharField(_('Pays'), max_length=100, default='Togo')
    
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6
    )
    
    # Horaires d'ouverture (JSON format)
    opening_hours = models.JSONField(
        _('Horaires d\'ouverture'),
        default=dict,
        help_text=_('Format: {"lundi": {"open": "08:00", "close": "22:00", "closed": false}, ...}')
    )
    
    # Informations de livraison
    delivery_radius = models.PositiveIntegerField(
        _('Rayon de livraison (km)'),
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    delivery_fee = models.DecimalField(
        _('Frais de livraison'),
        max_digits=6,
        decimal_places=2,
        default=2.50
    )
    min_order_amount = models.DecimalField(
        _('Montant minimum de commande'),
        max_digits=6,
        decimal_places=2,
        default=10.00
    )
    
    # Évaluations
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(_('Nombre d\'avis'), default=0)
    
    # Statut et métadonnées
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(_('Restaurant vedette'), default=False)
    is_verified = models.BooleanField(_('Vérifié'), default=False)
    
    # Tags
    tags = TaggableManager(verbose_name=_('Tags'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Restaurant')
        verbose_name_plural = _('Restaurants')
        ordering = ['-is_featured', '-average_rating', 'name']
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('restaurants:detail', kwargs={'slug': self.slug})
    
    def is_open_now(self):
        """Vérifie si le restaurant est ouvert maintenant."""
        from django.utils import timezone
        import datetime
        
        now = timezone.localtime()
        day_name = now.strftime('%A').lower()
        current_time = now.time()
        
        if day_name in self.opening_hours:
            day_hours = self.opening_hours[day_name]
            if day_hours.get('closed', False):
                return False
            
            open_time = datetime.time.fromisoformat(day_hours.get('open', '00:00'))
            close_time = datetime.time.fromisoformat(day_hours.get('close', '23:59'))
            
            return open_time <= current_time <= close_time
        
        return False
    
    def get_full_address(self):
        """Retourne l'adresse complète formatée."""
        return f"{self.address}, {self.city} {self.postal_code}, {self.country}"


class MenuItem(models.Model):
    """
    Éléments du menu des restaurants.
    """
    CATEGORY_CHOICES = [
        ('appetizer', _('Entrée')),
        ('main', _('Plat principal')),
        ('dessert', _('Dessert')),
        ('drink', _('Boisson')),
        ('side', _('Accompagnement')),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    
    # Informations de base
    name = models.CharField(_('Nom du plat'), max_length=200)
    slug = models.SlugField(_('Slug'))
    description = models.TextField(_('Description'))
    category = models.CharField(_('Catégorie'), max_length=20, choices=CATEGORY_CHOICES)
    
    # Images
    image = models.CharField(_('Image'), max_length=255, blank=True)
    
    # Prix et disponibilité
    price = models.DecimalField(
        _('Prix'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_available = models.BooleanField(_('Disponible'), default=True)
    
    # Informations nutritionnelles
    ingredients = models.TextField(_('Ingrédients'), blank=True)
    allergens = models.JSONField(
        _('Allergènes'),
        default=list,
        blank=True,
        help_text=_('Liste des allergènes présents')
    )
    calories = models.PositiveIntegerField(_('Calories'), blank=True, null=True)
    
    # Options de personnalisation
    customization_options = models.JSONField(
        _('Options de personnalisation'),
        default=dict,
        blank=True,
        help_text=_('Options disponibles pour personnaliser le plat')
    )
    
    # Popularité et promotions
    is_popular = models.BooleanField(_('Plat populaire'), default=False)
    is_spicy = models.BooleanField(_('Épicé'), default=False)
    is_vegetarian = models.BooleanField(_('Végétarien'), default=False)
    is_vegan = models.BooleanField(_('Végan'), default=False)
    is_halal = models.BooleanField(_('Halal'), default=False)
    
    # Promotion
    discount_percentage = models.DecimalField(
        _('Pourcentage de remise'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Temps de préparation
    preparation_time = models.PositiveIntegerField(
        _('Temps de préparation (minutes)'),
        default=15
    )
    
    # Tags
    tags = TaggableManager(verbose_name=_('Tags'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Élément du menu')
        verbose_name_plural = _('Éléments du menu')
        unique_together = ['restaurant', 'slug']
        ordering = ['category', 'name']
        
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('restaurants:menu_item', kwargs={
            'restaurant_slug': self.restaurant.slug,
            'slug': self.slug
        })
    
    def get_discounted_price(self):
        """Calcule le prix après remise."""
        if self.discount_percentage > 0:
            discount_amount = (self.price * self.discount_percentage) / 100
            return self.price - discount_amount
        return self.price
    
    def is_on_sale(self):
        """Vérifie si l'élément est en promotion."""
        return self.discount_percentage > 0


class RestaurantImage(models.Model):
    """
    Images additionnelles pour les restaurants.
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.CharField(_('Image'), max_length=255, blank=True)
    caption = models.CharField(_('Légende'), max_length=200, blank=True)
    is_featured = models.BooleanField(_('Image vedette'), default=False)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Image de restaurant')
        verbose_name_plural = _('Images de restaurants')
        ordering = ['-is_featured', '-created_at']
        
    def __str__(self):
        return f"{self.restaurant.name} - Image {self.id}"


class RestaurantStaff(models.Model):
    """
    Personnel des restaurants (gestionnaires, employés).
    """
    ROLE_CHOICES = [
        ('manager', _('Gestionnaire')),
        ('chef', _('Chef')),
        ('waiter', _('Serveur')),
        ('cashier', _('Caissier')),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='staff'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='restaurant_roles'
    )
    
    role = models.CharField(_('Rôle'), max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Permissions
    can_manage_menu = models.BooleanField(_('Peut gérer le menu'), default=False)
    can_manage_orders = models.BooleanField(_('Peut gérer les commandes'), default=True)
    can_view_analytics = models.BooleanField(_('Peut voir les statistiques'), default=False)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Personnel de restaurant')
        verbose_name_plural = _('Personnel de restaurants')
        unique_together = ['restaurant', 'user']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.restaurant.name} ({self.get_role_display()})"


class SpecialOffer(models.Model):
    """
    Offres spéciales et promotions des restaurants.
    """
    OFFER_TYPE_CHOICES = [
        ('percentage', _('Pourcentage de remise')),
        ('fixed_amount', _('Montant fixe')),
        ('buy_one_get_one', _('Achetez-en un, obtenez-en un')),
        ('free_delivery', _('Livraison gratuite')),
    ]
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='special_offers'
    )
    
    # Détails de l'offre
    title = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    offer_type = models.CharField(_('Type d\'offre'), max_length=20, choices=OFFER_TYPE_CHOICES)
    
    # Valeur de l'offre
    discount_value = models.DecimalField(
        _('Valeur de la remise'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    
    # Conditions
    min_order_amount = models.DecimalField(
        _('Montant minimum de commande'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    max_uses = models.PositiveIntegerField(_('Utilisations maximum'), blank=True, null=True)
    current_uses = models.PositiveIntegerField(_('Utilisations actuelles'), default=0)
    
    # Éléments du menu concernés
    applicable_items = models.ManyToManyField(
        MenuItem,
        verbose_name=_('Éléments concernés'),
        blank=True,
        related_name='special_offers'
    )
    
    # Période de validité
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'))
    
    # Jours de la semaine applicables
    applicable_days = models.JSONField(
        _('Jours applicables'),
        default=list,
        help_text=_('Liste des jours : ["monday", "tuesday", ...]')
    )
    
    # Heures applicables
    start_time = models.TimeField(_('Heure de début'), blank=True, null=True)
    end_time = models.TimeField(_('Heure de fin'), blank=True, null=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Offre spéciale')
        verbose_name_plural = _('Offres spéciales')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.restaurant.name} - {self.title}"
    
    def is_valid_now(self):
        """Vérifie si l'offre est valide maintenant."""
        from django.utils import timezone
        
        now = timezone.now()
        
        # Vérifier les dates
        if not (self.start_date <= now <= self.end_date):
            return False
        
        # Vérifier le jour de la semaine
        if self.applicable_days:
            current_day = now.strftime('%A').lower()
            if current_day not in self.applicable_days:
                return False
        
        # Vérifier les heures
        if self.start_time and self.end_time:
            current_time = now.time()
            if not (self.start_time <= current_time <= self.end_time):
                return False
        
        # Vérifier les utilisations
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return self.is_active
    
    def can_be_used(self, order_amount=0):
        """Vérifie si l'offre peut être utilisée pour un montant donné."""
        return self.is_valid_now() and order_amount >= self.min_order_amount
