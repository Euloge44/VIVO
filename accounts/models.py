"""
Modèles pour la gestion des utilisateurs de GourmetGuide.
Support de 4 types d'utilisateurs : Client, Restaurant, Livreur, Admin.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.urls import reverse


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé qui étend AbstractUser.
    Support de différents types d'utilisateurs avec leurs spécificités.
    """
    
    USER_TYPE_CHOICES = [
        ('client', _('Client')),
        ('restaurant', _('Restaurant')),
        ('delivery', _('Livreur')),
        ('admin', _('Administrateur')),
    ]
    
    LANGUAGE_CHOICES = [
        ('fr', _('Français')),
        ('en', _('English')),
    ]
    
    # Champs obligatoires
    email = models.EmailField(_('Email'), unique=True)
    user_type = models.CharField(
        _('Type d\'utilisateur'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='client'
    )
    
    # Informations de contact
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{8,15}$',
        message=_('Le numéro de téléphone doit être au format: "+999999999". Jusqu\'à 15 chiffres autorisés.')
    )
    phone = models.CharField(
        _('Téléphone'),
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    
    # Informations de profil
    profile_image = models.CharField(
        _('Photo de profil'),
        max_length=255,
        blank=True,
        help_text=_('URL de la photo de profil')
    )
    
    # Statut et préférences
    is_verified = models.BooleanField(_('Vérifié'), default=False)
    language_preference = models.CharField(
        _('Langue préférée'),
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='fr'
    )
    
    # Informations d'adresse
    address = models.TextField(_('Adresse'), blank=True)
    city = models.CharField(_('Ville'), max_length=100, blank=True)
    postal_code = models.CharField(_('Code postal'), max_length=10, blank=True)
    country = models.CharField(_('Pays'), max_length=100, default='Togo')
    
    # Géolocalisation
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('Dernière IP de connexion'), blank=True, null=True)
    
    # Configuration email comme nom d'utilisateur
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'user_type']
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        db_table = 'accounts_user'
        
    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_user_type_display()})"
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'pk': self.pk})
    
    def get_full_address(self):
        """Retourne l'adresse complète formatée."""
        parts = [self.address, self.city, self.postal_code, self.country]
        return ', '.join([part for part in parts if part])
    
    def has_location(self):
        """Vérifie si l'utilisateur a des coordonnées GPS."""
        return self.latitude is not None and self.longitude is not None
    
    def is_client(self):
        return self.user_type == 'client'
    
    def is_restaurant(self):
        return self.user_type == 'restaurant'
    
    def is_delivery_person(self):
        return self.user_type == 'delivery'
    
    def is_admin_user(self):
        return self.user_type == 'admin'


class UserProfile(models.Model):
    """
    Profil étendu pour informations additionnelles utilisateur.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Préférences alimentaires
    dietary_preferences = models.JSONField(
        _('Préférences alimentaires'),
        default=list,
        blank=True,
        help_text=_('Liste des préférences : végétarien, végan, halal, etc.')
    )
    
    # Allergies
    allergies = models.JSONField(
        _('Allergies'),
        default=list,
        blank=True,
        help_text=_('Liste des allergies alimentaires')
    )
    
    # Préférences de notification
    email_notifications = models.BooleanField(_('Notifications email'), default=True)
    sms_notifications = models.BooleanField(_('Notifications SMS'), default=False)
    push_notifications = models.BooleanField(_('Notifications push'), default=True)
    
    # Informations de livraison par défaut
    default_delivery_address = models.TextField(_('Adresse de livraison par défaut'), blank=True)
    delivery_instructions = models.TextField(_('Instructions de livraison'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateurs')
        
    def __str__(self):
        return f"Profil de {self.user.email}"


class UserDevice(models.Model):
    """
    Modèle pour gérer les appareils des utilisateurs (notifications push).
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    
    device_id = models.CharField(_('ID de l\'appareil'), max_length=255, unique=True)
    device_type = models.CharField(
        _('Type d\'appareil'),
        max_length=20,
        choices=[
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web'),
        ]
    )
    
    # Token pour notifications push
    push_token = models.TextField(_('Token push'), blank=True)
    
    # Informations sur l'appareil
    device_name = models.CharField(_('Nom de l\'appareil'), max_length=100, blank=True)
    app_version = models.CharField(_('Version de l\'app'), max_length=20, blank=True)
    os_version = models.CharField(_('Version OS'), max_length=50, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    last_used = models.DateTimeField(_('Dernière utilisation'), auto_now=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Appareil utilisateur')
        verbose_name_plural = _('Appareils utilisateurs')
        unique_together = ['user', 'device_id']
        
    def __str__(self):
        return f"{self.user.email} - {self.device_name or self.device_type}"
