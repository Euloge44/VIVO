"""
Modèles pour la gestion des livraisons de GourmetGuide.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class DeliveryPerson(models.Model):
    """
    Profil étendu pour les livreurs.
    """
    STATUS_CHOICES = [
        ('available', _('Disponible')),
        ('busy', _('Occupé')),
        ('offline', _('Hors ligne')),
        ('break', _('En pause')),
    ]
    
    VEHICLE_CHOICES = [
        ('bike', _('Vélo')),
        ('motorbike', _('Moto')),
        ('car', _('Voiture')),
        ('scooter', _('Scooter')),
        ('walking', _('À pied')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='delivery_profile',
        limit_choices_to={'user_type': 'delivery'}
    )
    
    # Informations personnelles
    license_number = models.CharField(_('Numéro de permis'), max_length=50, blank=True)
    vehicle_type = models.CharField(_('Type de véhicule'), max_length=20, choices=VEHICLE_CHOICES)
    vehicle_registration = models.CharField(_('Immatriculation'), max_length=20, blank=True)
    
    # Documents
    identity_document = models.CharField(_('Pièce d\'identité'), max_length=255, blank=True)
    license_document = models.CharField(_('Permis de conduire'), max_length=255, blank=True)
    vehicle_insurance = models.CharField(_('Assurance véhicule'), max_length=255, blank=True)
    
    # Statut et localisation
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='offline')
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
    last_location_update = models.DateTimeField(_('Dernière mise à jour de position'), blank=True, null=True)
    
    # Zone de travail
    working_city = models.ForeignKey(
        'core.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_persons'
    )
    max_delivery_radius = models.PositiveIntegerField(
        _('Rayon de livraison maximum (km)'),
        default=10
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
    
    # Statistiques
    total_deliveries = models.PositiveIntegerField(_('Livraisons totales'), default=0)
    successful_deliveries = models.PositiveIntegerField(_('Livraisons réussies'), default=0)
    
    # Vérification
    is_verified = models.BooleanField(_('Vérifié'), default=False)
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Livreur')
        verbose_name_plural = _('Livreurs')
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_vehicle_type_display()}"
    
    def get_success_rate(self):
        """Calcule le taux de réussite des livraisons."""
        if self.total_deliveries > 0:
            return (self.successful_deliveries / self.total_deliveries) * 100
        return 0
    
    def is_available_for_delivery(self):
        """Vérifie si le livreur est disponible."""
        return self.status == 'available' and self.is_active and self.is_verified
    
    def update_location(self, latitude, longitude):
        """Met à jour la position du livreur."""
        from django.utils import timezone
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])


class DeliveryZone(models.Model):
    """
    Zones de livraison définies pour optimiser les attributions.
    """
    name = models.CharField(_('Nom de la zone'), max_length=100)
    city = models.ForeignKey(
        'core.City',
        on_delete=models.CASCADE,
        related_name='delivery_zones'
    )
    
    # Coordonnées de la zone (polygone ou cercle)
    center_latitude = models.DecimalField(
        _('Latitude du centre'),
        max_digits=9,
        decimal_places=6
    )
    center_longitude = models.DecimalField(
        _('Longitude du centre'),
        max_digits=9,
        decimal_places=6
    )
    radius = models.PositiveIntegerField(_('Rayon (km)'), default=5)
    
    # Frais de livraison spécifiques à la zone
    delivery_fee = models.DecimalField(
        _('Frais de livraison'),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Livreurs assignés à cette zone
    assigned_delivery_persons = models.ManyToManyField(
        DeliveryPerson,
        verbose_name=_('Livreurs assignés'),
        blank=True,
        related_name='assigned_zones'
    )
    
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Zone de livraison')
        verbose_name_plural = _('Zones de livraison')
        ordering = ['city', 'name']
        
    def __str__(self):
        return f"{self.name} - {self.city.name}"


class DeliveryAssignment(models.Model):
    """
    Attribution des commandes aux livreurs.
    """
    STATUS_CHOICES = [
        ('assigned', _('Assignée')),
        ('accepted', _('Acceptée')),
        ('rejected', _('Refusée')),
        ('picked_up', _('Récupérée')),
        ('delivered', _('Livrée')),
        ('cancelled', _('Annulée')),
    ]
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_assignment'
    )
    delivery_person = models.ForeignKey(
        DeliveryPerson,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Statut et temps
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(_('Assigné le'), auto_now_add=True)
    accepted_at = models.DateTimeField(_('Accepté le'), blank=True, null=True)
    picked_up_at = models.DateTimeField(_('Récupéré le'), blank=True, null=True)
    delivered_at = models.DateTimeField(_('Livré le'), blank=True, null=True)
    
    # Estimations
    estimated_pickup_time = models.DateTimeField(_('Heure de récupération estimée'), blank=True, null=True)
    estimated_delivery_time = models.DateTimeField(_('Heure de livraison estimée'), blank=True, null=True)
    
    # Distance et temps
    distance_to_restaurant = models.DecimalField(
        _('Distance jusqu\'au restaurant (km)'),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    distance_to_customer = models.DecimalField(
        _('Distance jusqu\'au client (km)'),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Notes
    delivery_notes = models.TextField(_('Notes de livraison'), blank=True)
    rejection_reason = models.TextField(_('Raison du refus'), blank=True)
    
    # Métadonnées
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Attribution de livraison')
        verbose_name_plural = _('Attributions de livraisons')
        ordering = ['-assigned_at']
        
    def __str__(self):
        return f"Livraison {self.order.order_number} → {self.delivery_person.user.get_full_name()}"
    
    def get_total_distance(self):
        """Calcule la distance totale de livraison."""
        if self.distance_to_restaurant and self.distance_to_customer:
            return self.distance_to_restaurant + self.distance_to_customer
        return None
    
    def get_delivery_duration(self):
        """Calcule la durée de livraison."""
        if self.delivered_at and self.picked_up_at:
            return (self.delivered_at - self.picked_up_at).total_seconds() / 60
        return None


class DeliveryRoute(models.Model):
    """
    Itinéraires de livraison pour optimisation.
    """
    delivery_person = models.ForeignKey(
        DeliveryPerson,
        on_delete=models.CASCADE,
        related_name='routes'
    )
    
    # Ordres dans l'itinéraire
    orders = models.ManyToManyField(
        'orders.Order',
        through='DeliveryRouteOrder',
        related_name='delivery_routes'
    )
    
    # Informations de l'itinéraire
    start_time = models.DateTimeField(_('Heure de début'))
    estimated_end_time = models.DateTimeField(_('Heure de fin estimée'), blank=True, null=True)
    actual_end_time = models.DateTimeField(_('Heure de fin réelle'), blank=True, null=True)
    
    # Distance et optimisation
    total_distance = models.DecimalField(
        _('Distance totale (km)'),
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    estimated_duration = models.PositiveIntegerField(_('Durée estimée (minutes)'), blank=True, null=True)
    
    # Statut
    is_optimized = models.BooleanField(_('Optimisé'), default=False)
    is_completed = models.BooleanField(_('Terminé'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Itinéraire de livraison')
        verbose_name_plural = _('Itinéraires de livraisons')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Itinéraire {self.id} - {self.delivery_person.user.get_full_name()}"


class DeliveryRouteOrder(models.Model):
    """
    Ordre des commandes dans un itinéraire de livraison.
    """
    route = models.ForeignKey(
        DeliveryRoute,
        on_delete=models.CASCADE,
        related_name='route_orders'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='route_positions'
    )
    
    # Position dans l'itinéraire
    sequence_order = models.PositiveIntegerField(_('Ordre dans la séquence'))
    
    # Temps estimés
    estimated_arrival_time = models.DateTimeField(_('Heure d\'arrivée estimée'), blank=True, null=True)
    actual_arrival_time = models.DateTimeField(_('Heure d\'arrivée réelle'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Commande dans itinéraire')
        verbose_name_plural = _('Commandes dans itinéraires')
        unique_together = ['route', 'order']
        ordering = ['sequence_order']
        
    def __str__(self):
        return f"#{self.sequence_order} - Commande {self.order.order_number}"


class DeliveryFeedback(models.Model):
    """
    Retours sur les livraisons.
    """
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_feedback'
    )
    delivery_person = models.ForeignKey(
        DeliveryPerson,
        on_delete=models.CASCADE,
        related_name='feedback_received'
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delivery_feedback_given',
        limit_choices_to={'user_type': 'client'}
    )
    
    # Évaluations
    delivery_rating = models.PositiveIntegerField(
        _('Note de livraison'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    punctuality_rating = models.PositiveIntegerField(
        _('Note de ponctualité'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    politeness_rating = models.PositiveIntegerField(
        _('Note de politesse'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Commentaires
    comment = models.TextField(_('Commentaire'), blank=True)
    
    # Problèmes signalés
    reported_issues = models.JSONField(
        _('Problèmes signalés'),
        default=list,
        blank=True,
        help_text=_('Liste des problèmes : retard, nourriture froide, etc.')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Retour de livraison')
        verbose_name_plural = _('Retours de livraisons')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Retour - Commande {self.order.order_number}"
    
    def get_average_rating(self):
        """Calcule la note moyenne globale."""
        return (self.delivery_rating + self.punctuality_rating + self.politeness_rating) / 3


class DeliveryPerformance(models.Model):
    """
    Statistiques de performance des livreurs.
    """
    delivery_person = models.OneToOneField(
        DeliveryPerson,
        on_delete=models.CASCADE,
        related_name='performance'
    )
    
    # Statistiques temporelles
    average_delivery_time = models.DecimalField(
        _('Temps de livraison moyen (minutes)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    average_pickup_time = models.DecimalField(
        _('Temps de récupération moyen (minutes)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    
    # Statistiques de distance
    total_distance_covered = models.DecimalField(
        _('Distance totale parcourue (km)'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    average_distance_per_delivery = models.DecimalField(
        _('Distance moyenne par livraison (km)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    
    # Statistiques de ponctualité
    on_time_deliveries = models.PositiveIntegerField(_('Livraisons à l\'heure'), default=0)
    late_deliveries = models.PositiveIntegerField(_('Livraisons en retard'), default=0)
    
    # Revenus
    total_earnings = models.DecimalField(
        _('Gains totaux'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Période de calcul
    calculation_period_start = models.DateField(_('Début de période'))
    calculation_period_end = models.DateField(_('Fin de période'))
    
    # Métadonnées
    last_calculated = models.DateTimeField(_('Dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('Performance de livreur')
        verbose_name_plural = _('Performances de livreurs')
        
    def __str__(self):
        return f"Performance - {self.delivery_person.user.get_full_name()}"
    
    def get_punctuality_rate(self):
        """Calcule le taux de ponctualité."""
        total = self.on_time_deliveries + self.late_deliveries
        if total > 0:
            return (self.on_time_deliveries / total) * 100
        return 0


class DeliveryIncident(models.Model):
    """
    Incidents de livraison signalés.
    """
    INCIDENT_TYPE_CHOICES = [
        ('accident', _('Accident')),
        ('vehicle_breakdown', _('Panne de véhicule')),
        ('weather', _('Conditions météo')),
        ('traffic', _('Embouteillages')),
        ('customer_unavailable', _('Client indisponible')),
        ('wrong_address', _('Adresse incorrecte')),
        ('food_spilled', _('Nourriture renversée')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('reported', _('Signalé')),
        ('investigating', _('En cours d\'investigation')),
        ('resolved', _('Résolu')),
        ('closed', _('Fermé')),
    ]
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_incidents'
    )
    delivery_person = models.ForeignKey(
        DeliveryPerson,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    
    # Type et description
    incident_type = models.CharField(_('Type d\'incident'), max_length=30, choices=INCIDENT_TYPE_CHOICES)
    description = models.TextField(_('Description'))
    
    # Localisation de l'incident
    incident_latitude = models.DecimalField(
        _('Latitude de l\'incident'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    incident_longitude = models.DecimalField(
        _('Longitude de l\'incident'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Photos de l'incident
    incident_photos = models.JSONField(
        _('Photos de l\'incident'),
        default=list,
        blank=True
    )
    
    # Statut et résolution
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='reported')
    resolution_notes = models.TextField(_('Notes de résolution'), blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_incidents',
        limit_choices_to={'user_type': 'admin'}
    )
    
    # Métadonnées
    reported_at = models.DateTimeField(_('Signalé le'), auto_now_add=True)
    resolved_at = models.DateTimeField(_('Résolu le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Incident de livraison')
        verbose_name_plural = _('Incidents de livraisons')
        ordering = ['-reported_at']
        
    def __str__(self):
        return f"Incident {self.get_incident_type_display()} - Commande {self.order.order_number}"
