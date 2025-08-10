"""
Modèles pour le système de notifications de GourmetGuide.
Support notifications push, email, SMS et temps réel.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """
    Modèle principal pour les notifications.
    """
    TYPE_CHOICES = [
        ('order_status', _('Statut de commande')),
        ('payment_status', _('Statut de paiement')),
        ('delivery_update', _('Mise à jour livraison')),
        ('promotion', _('Promotion')),
        ('loyalty_update', _('Mise à jour fidélité')),
        ('review_request', _('Demande d\'avis')),
        ('system_update', _('Mise à jour système')),
        ('welcome', _('Bienvenue')),
        ('reminder', _('Rappel')),
        ('alert', _('Alerte')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Basse')),
        ('normal', _('Normale')),
        ('high', _('Haute')),
        ('urgent', _('Urgente')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('sent', _('Envoyée')),
        ('delivered', _('Livrée')),
        ('read', _('Lue')),
        ('failed', _('Échouée')),
        ('cancelled', _('Annulée')),
    ]
    
    # Relations
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    
    # Contenu
    notification_type = models.CharField(_('Type'), max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(_('Titre'), max_length=200)
    message = models.TextField(_('Message'))
    
    # Métadonnées
    data = models.JSONField(
        _('Données additionnelles'),
        default=dict,
        blank=True,
        help_text=_('Données pour actions ou deep links')
    )
    
    # Priorité et canaux
    priority = models.CharField(_('Priorité'), max_length=10, choices=PRIORITY_CHOICES, default='normal')
    send_push = models.BooleanField(_('Envoyer push'), default=True)
    send_email = models.BooleanField(_('Envoyer email'), default=False)
    send_sms = models.BooleanField(_('Envoyer SMS'), default=False)
    
    # Statut et tracking
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Actions
    action_url = models.URLField(_('URL d\'action'), blank=True)
    action_text = models.CharField(_('Texte d\'action'), max_length=50, blank=True)
    
    # Références
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Timing
    scheduled_for = models.DateTimeField(_('Programmé pour'), blank=True, null=True)
    expires_at = models.DateTimeField(_('Expire le'), blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    sent_at = models.DateTimeField(_('Envoyé le'), blank=True, null=True)
    read_at = models.DateTimeField(_('Lu le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'scheduled_for']),
        ]
        
    def __str__(self):
        return f"{self.title} → {self.recipient.email}"
    
    def mark_as_read(self):
        """Marque la notification comme lue."""
        if self.status != 'read':
            from django.utils import timezone
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def is_expired(self):
        """Vérifie si la notification a expiré."""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class NotificationTemplate(models.Model):
    """
    Templates pour les notifications automatiques.
    """
    # Identification
    code = models.CharField(_('Code'), max_length=50, unique=True)
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Contenu du template
    title_template = models.CharField(_('Template du titre'), max_length=200)
    message_template = models.TextField(_('Template du message'))
    
    # Configuration des canaux
    default_send_push = models.BooleanField(_('Push par défaut'), default=True)
    default_send_email = models.BooleanField(_('Email par défaut'), default=False)
    default_send_sms = models.BooleanField(_('SMS par défaut'), default=False)
    
    # Priorité par défaut
    default_priority = models.CharField(
        _('Priorité par défaut'),
        max_length=10,
        choices=Notification.PRIORITY_CHOICES,
        default='normal'
    )
    
    # Type de notification
    notification_type = models.CharField(
        _('Type de notification'),
        max_length=20,
        choices=Notification.TYPE_CHOICES
    )
    
    # Langue
    language = models.CharField(_('Langue'), max_length=5, default='fr')
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Template de notification')
        verbose_name_plural = _('Templates de notifications')
        unique_together = ['code', 'language']
        ordering = ['notification_type', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.language})"
    
    def render(self, context=None):
        """Rend le template avec le contexte donné."""
        if not context:
            context = {}
        
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        
        return title, message


class NotificationPreference(models.Model):
    """
    Préférences de notification des utilisateurs.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Préférences par type de notification
    order_status_push = models.BooleanField(_('Push statut commande'), default=True)
    order_status_email = models.BooleanField(_('Email statut commande'), default=True)
    order_status_sms = models.BooleanField(_('SMS statut commande'), default=False)
    
    payment_status_push = models.BooleanField(_('Push statut paiement'), default=True)
    payment_status_email = models.BooleanField(_('Email statut paiement'), default=False)
    payment_status_sms = models.BooleanField(_('SMS statut paiement'), default=False)
    
    delivery_update_push = models.BooleanField(_('Push livraison'), default=True)
    delivery_update_email = models.BooleanField(_('Email livraison'), default=False)
    delivery_update_sms = models.BooleanField(_('SMS livraison'), default=True)
    
    promotion_push = models.BooleanField(_('Push promotions'), default=True)
    promotion_email = models.BooleanField(_('Email promotions'), default=True)
    promotion_sms = models.BooleanField(_('SMS promotions'), default=False)
    
    loyalty_update_push = models.BooleanField(_('Push fidélité'), default=True)
    loyalty_update_email = models.BooleanField(_('Email fidélité'), default=False)
    loyalty_update_sms = models.BooleanField(_('SMS fidélité'), default=False)
    
    # Horaires de notification
    quiet_hours_start = models.TimeField(_('Début heures silencieuses'), default='22:00')
    quiet_hours_end = models.TimeField(_('Fin heures silencieuses'), default='08:00')
    
    # Fréquence
    max_daily_notifications = models.PositiveIntegerField(_('Maximum notifications/jour'), default=10)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Préférences de notification')
        verbose_name_plural = _('Préférences de notifications')
        
    def __str__(self):
        return f"Préférences de {self.user.email}"
    
    def should_send_notification(self, notification_type, channel):
        """Vérifie si une notification doit être envoyée."""
        from django.utils import timezone
        
        # Vérifier les heures silencieuses
        now = timezone.localtime().time()
        if self.quiet_hours_start <= now or now <= self.quiet_hours_end:
            if channel in ['push', 'sms']:  # Email peut être envoyé même pendant les heures silencieuses
                return False
        
        # Vérifier les préférences spécifiques
        preference_field = f"{notification_type}_{channel}"
        return getattr(self, preference_field, False)


class PushNotificationDevice(models.Model):
    """
    Appareils enregistrés pour les notifications push.
    """
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_devices'
    )
    
    # Informations de l'appareil
    device_token = models.TextField(_('Token de l\'appareil'))
    platform = models.CharField(_('Plateforme'), max_length=10, choices=PLATFORM_CHOICES)
    device_id = models.CharField(_('ID de l\'appareil'), max_length=255)
    
    # Métadonnées de l'appareil
    device_name = models.CharField(_('Nom de l\'appareil'), max_length=100, blank=True)
    app_version = models.CharField(_('Version de l\'app'), max_length=20, blank=True)
    os_version = models.CharField(_('Version OS'), max_length=50, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    registered_at = models.DateTimeField(_('Enregistré le'), auto_now_add=True)
    last_used = models.DateTimeField(_('Dernière utilisation'), auto_now=True)
    
    class Meta:
        verbose_name = _('Appareil push')
        verbose_name_plural = _('Appareils push')
        unique_together = ['user', 'device_id']
        ordering = ['-last_used']
        
    def __str__(self):
        return f"{self.user.email} - {self.device_name or self.platform}"


class NotificationLog(models.Model):
    """
    Log des notifications envoyées.
    """
    CHANNEL_CHOICES = [
        ('push', _('Push')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('websocket', _('WebSocket')),
    ]
    
    STATUS_CHOICES = [
        ('sent', _('Envoyé')),
        ('delivered', _('Livré')),
        ('failed', _('Échoué')),
        ('bounced', _('Rejeté')),
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    
    # Canal et statut
    channel = models.CharField(_('Canal'), max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES)
    
    # Détails de livraison
    recipient_address = models.CharField(_('Adresse destinataire'), max_length=255)
    external_id = models.CharField(_('ID externe'), max_length=200, blank=True)
    
    # Réponse du fournisseur
    provider_response = models.JSONField(
        _('Réponse du fournisseur'),
        default=dict,
        blank=True
    )
    
    # Erreurs
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    error_code = models.CharField(_('Code d\'erreur'), max_length=50, blank=True)
    
    # Métadonnées
    sent_at = models.DateTimeField(_('Envoyé le'), auto_now_add=True)
    delivered_at = models.DateTimeField(_('Livré le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Log de notification')
        verbose_name_plural = _('Logs de notifications')
        ordering = ['-sent_at']
        
    def __str__(self):
        return f"{self.get_channel_display()} → {self.recipient_address} ({self.status})"


class NotificationCampaign(models.Model):
    """
    Campagnes de notifications marketing.
    """
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('scheduled', _('Programmée')),
        ('sending', _('En cours d\'envoi')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
        ('failed', _('Échouée')),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('all_users', _('Tous les utilisateurs')),
        ('clients', _('Clients uniquement')),
        ('restaurants', _('Restaurants uniquement')),
        ('delivery_persons', _('Livreurs uniquement')),
        ('loyalty_tier', _('Niveau de fidélité spécifique')),
        ('city', _('Ville spécifique')),
        ('inactive_users', _('Utilisateurs inactifs')),
        ('custom', _('Sélection personnalisée')),
    ]
    
    # Informations de base
    name = models.CharField(_('Nom de la campagne'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Contenu
    title = models.CharField(_('Titre'), max_length=200)
    message = models.TextField(_('Message'))
    image = models.CharField(_('Image'), max_length=255, blank=True)
    
    # Ciblage
    target_type = models.CharField(_('Type de cible'), max_length=20, choices=TARGET_TYPE_CHOICES)
    target_criteria = models.JSONField(
        _('Critères de ciblage'),
        default=dict,
        blank=True,
        help_text=_('Critères spécifiques selon le type de cible')
    )
    
    # Utilisateurs spécifiques (pour ciblage personnalisé)
    target_users = models.ManyToManyField(
        User,
        verbose_name=_('Utilisateurs ciblés'),
        blank=True,
        related_name='targeted_campaigns'
    )
    
    # Canaux
    send_push = models.BooleanField(_('Envoyer push'), default=True)
    send_email = models.BooleanField(_('Envoyer email'), default=False)
    send_sms = models.BooleanField(_('Envoyer SMS'), default=False)
    
    # Programmation
    scheduled_for = models.DateTimeField(_('Programmé pour'), blank=True, null=True)
    
    # Statut et statistiques
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    total_recipients = models.PositiveIntegerField(_('Destinataires totaux'), default=0)
    sent_count = models.PositiveIntegerField(_('Envoyés'), default=0)
    delivered_count = models.PositiveIntegerField(_('Livrés'), default=0)
    failed_count = models.PositiveIntegerField(_('Échoués'), default=0)
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_campaigns',
        limit_choices_to={'user_type': 'admin'}
    )
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    started_at = models.DateTimeField(_('Démarré le'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Terminé le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Campagne de notifications')
        verbose_name_plural = _('Campagnes de notifications')
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def get_target_users(self):
        """Retourne les utilisateurs ciblés par la campagne."""
        if self.target_type == 'all_users':
            return User.objects.filter(is_active=True)
        elif self.target_type == 'clients':
            return User.objects.filter(user_type='client', is_active=True)
        elif self.target_type == 'restaurants':
            return User.objects.filter(user_type='restaurant', is_active=True)
        elif self.target_type == 'delivery_persons':
            return User.objects.filter(user_type='delivery', is_active=True)
        elif self.target_type == 'custom':
            return self.target_users.all()
        # Ajouter d'autres logiques de ciblage selon les besoins
        return User.objects.none()


class EmailTemplate(models.Model):
    """
    Templates d'emails pour les notifications.
    """
    # Identification
    code = models.CharField(_('Code'), max_length=50, unique=True)
    name = models.CharField(_('Nom'), max_length=200)
    
    # Contenu email
    subject_template = models.CharField(_('Template du sujet'), max_length=200)
    html_template = models.TextField(_('Template HTML'))
    text_template = models.TextField(_('Template texte'), blank=True)
    
    # Type de notification associé
    notification_type = models.CharField(
        _('Type de notification'),
        max_length=20,
        choices=Notification.TYPE_CHOICES
    )
    
    # Langue
    language = models.CharField(_('Langue'), max_length=5, default='fr')
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Template d\'email')
        verbose_name_plural = _('Templates d\'emails')
        unique_together = ['code', 'language']
        ordering = ['notification_type', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.language})"


class SMSTemplate(models.Model):
    """
    Templates de SMS pour les notifications.
    """
    # Identification
    code = models.CharField(_('Code'), max_length=50, unique=True)
    name = models.CharField(_('Nom'), max_length=200)
    
    # Contenu SMS (limité à 160 caractères)
    message_template = models.CharField(_('Template du message'), max_length=160)
    
    # Type de notification associé
    notification_type = models.CharField(
        _('Type de notification'),
        max_length=20,
        choices=Notification.TYPE_CHOICES
    )
    
    # Langue
    language = models.CharField(_('Langue'), max_length=5, default='fr')
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Template de SMS')
        verbose_name_plural = _('Templates de SMS')
        unique_together = ['code', 'language']
        ordering = ['notification_type', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.language})"
    
    def render(self, context=None):
        """Rend le template SMS avec le contexte donné."""
        if not context:
            context = {}
        return self.message_template.format(**context)[:160]  # Limiter à 160 caractères
