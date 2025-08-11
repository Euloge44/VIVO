"""
Modèles utilitaires pour l'application GourmetGuide.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class SiteSettings(models.Model):
    """
    Paramètres globaux du site.
    """
    # Informations générales
    site_name = models.CharField(_('Nom du site'), max_length=100, default='GourmetGuide')
    site_description = models.TextField(_('Description du site'), blank=True)
    site_logo = models.CharField(_('Logo du site'), max_length=255, blank=True)
    site_favicon = models.CharField(_('Favicon'), max_length=255, blank=True)
    
    # Contact
    contact_email = models.EmailField(_('Email de contact'), blank=True)
    contact_phone = models.CharField(_('Téléphone de contact'), max_length=20, blank=True)
    support_email = models.EmailField(_('Email de support'), blank=True)
    
    # Réseaux sociaux
    facebook_url = models.URLField(_('Facebook'), blank=True)
    twitter_url = models.URLField(_('Twitter'), blank=True)
    instagram_url = models.URLField(_('Instagram'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn'), blank=True)
    
    # Paramètres de commande
    default_delivery_fee = models.DecimalField(
        _('Frais de livraison par défaut'),
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
    max_delivery_radius = models.PositiveIntegerField(
        _('Rayon de livraison maximum (km)'),
        default=15
    )
    
    # Paramètres de fidélité
    loyalty_points_per_euro = models.PositiveIntegerField(
        _('Points de fidélité par euro'),
        default=10
    )
    loyalty_euro_per_point = models.DecimalField(
        _('Valeur en euro par point'),
        max_digits=4,
        decimal_places=3,
        default=0.01
    )
    
    # Taxes
    tax_rate = models.DecimalField(
        _('Taux de taxe (%)'),
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Paramètres de notification
    enable_email_notifications = models.BooleanField(_('Activer les notifications email'), default=True)
    enable_sms_notifications = models.BooleanField(_('Activer les notifications SMS'), default=False)
    enable_push_notifications = models.BooleanField(_('Activer les notifications push'), default=True)
    
    # Maintenance
    maintenance_mode = models.BooleanField(_('Mode maintenance'), default=False)
    maintenance_message = models.TextField(_('Message de maintenance'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Paramètres du site')
        verbose_name_plural = _('Paramètres du site')
        
    def __str__(self):
        return self.site_name
    
    @classmethod
    def get_settings(cls):
        """Retourne l'instance unique des paramètres."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class Country(models.Model):
    """
    Modèle pour les pays supportés.
    """
    name = models.CharField(_('Nom'), max_length=100)
    code = models.CharField(_('Code ISO'), max_length=3, unique=True)
    phone_prefix = models.CharField(_('Préfixe téléphonique'), max_length=5)
    currency_code = models.CharField(_('Code devise'), max_length=3, default='XOF')
    currency_symbol = models.CharField(_('Symbole devise'), max_length=5, default='CFA')
    
    # Support des paiements mobiles
    supports_tmoney = models.BooleanField(_('Support Tmoney'), default=False)
    supports_flooz = models.BooleanField(_('Support Flooz'), default=False)
    
    is_active = models.BooleanField(_('Actif'), default=True)
    
    class Meta:
        verbose_name = _('Pays')
        verbose_name_plural = _('Pays')
        ordering = ['name']
        
    def __str__(self):
        return self.name


class City(models.Model):
    """
    Modèle pour les villes supportées.
    """
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities'
    )
    name = models.CharField(_('Nom'), max_length=100)
    
    # Coordonnées du centre ville
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
    
    # Zone de couverture
    coverage_radius = models.PositiveIntegerField(
        _('Rayon de couverture (km)'),
        default=20
    )
    
    is_active = models.BooleanField(_('Actif'), default=True)
    
    class Meta:
        verbose_name = _('Ville')
        verbose_name_plural = _('Villes')
        unique_together = ['country', 'name']
        ordering = ['country', 'name']
        
    def __str__(self):
        return f"{self.name}, {self.country.name}"


class FAQ(models.Model):
    """
    Questions fréquemment posées.
    """
    CATEGORY_CHOICES = [
        ('general', _('Général')),
        ('ordering', _('Commandes')),
        ('payment', _('Paiements')),
        ('delivery', _('Livraison')),
        ('restaurant', _('Restaurants')),
        ('account', _('Compte')),
    ]
    
    category = models.CharField(_('Catégorie'), max_length=20, choices=CATEGORY_CHOICES)
    question = models.CharField(_('Question'), max_length=500)
    answer = models.TextField(_('Réponse'))
    
    # Ordre d'affichage
    order = models.PositiveIntegerField(_('Ordre'), default=0)
    
    # Langues
    language = models.CharField(_('Langue'), max_length=5, default='fr')
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['category', 'order', 'question']
        
    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    """
    Messages de contact des utilisateurs.
    """
    SUBJECT_CHOICES = [
        ('general', _('Question générale')),
        ('technical', _('Problème technique')),
        ('billing', _('Facturation')),
        ('restaurant', _('Restaurant')),
        ('delivery', _('Livraison')),
        ('complaint', _('Plainte')),
        ('suggestion', _('Suggestion')),
    ]
    
    STATUS_CHOICES = [
        ('new', _('Nouveau')),
        ('in_progress', _('En cours')),
        ('resolved', _('Résolu')),
        ('closed', _('Fermé')),
    ]
    
    # Informations de contact
    name = models.CharField(_('Nom'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Téléphone'), max_length=20, blank=True)
    
    # Message
    subject = models.CharField(_('Sujet'), max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField(_('Message'))
    
    # Utilisateur lié (optionnel)
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages'
    )
    
    # Statut et traitement
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_messages',
        limit_choices_to={'user_type': 'admin'}
    )
    admin_response = models.TextField(_('Réponse admin'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    resolved_at = models.DateTimeField(_('Résolu le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Message de contact')
        verbose_name_plural = _('Messages de contact')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"


class AppVersion(models.Model):
    """
    Gestion des versions de l'application.
    """
    PLATFORM_CHOICES = [
        ('web', _('Web')),
        ('android', _('Android')),
        ('ios', _('iOS')),
    ]
    
    platform = models.CharField(_('Plateforme'), max_length=10, choices=PLATFORM_CHOICES)
    version_number = models.CharField(_('Numéro de version'), max_length=20)
    version_code = models.PositiveIntegerField(_('Code de version'))
    
    # Informations de mise à jour
    is_required = models.BooleanField(_('Mise à jour obligatoire'), default=False)
    release_notes = models.TextField(_('Notes de version'), blank=True)
    download_url = models.URLField(_('URL de téléchargement'), blank=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    released_at = models.DateTimeField(_('Publié le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Version de l\'application')
        verbose_name_plural = _('Versions de l\'application')
        unique_together = ['platform', 'version_number']
        ordering = ['-version_code']
        
    def __str__(self):
        return f"{self.get_platform_display()} v{self.version_number}"
