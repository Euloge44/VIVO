"""
Modèles pour les analytics et statistiques de GourmetGuide.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class DailyStats(models.Model):
    """
    Statistiques quotidiennes globales de la plateforme.
    """
    date = models.DateField(_('Date'), unique=True)
    
    # Statistiques des commandes
    total_orders = models.PositiveIntegerField(_('Commandes totales'), default=0)
    completed_orders = models.PositiveIntegerField(_('Commandes terminées'), default=0)
    cancelled_orders = models.PositiveIntegerField(_('Commandes annulées'), default=0)
    
    # Revenus
    total_revenue = models.DecimalField(
        _('Revenus totaux'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    platform_commission = models.DecimalField(
        _('Commission plateforme'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Utilisateurs
    new_customers = models.PositiveIntegerField(_('Nouveaux clients'), default=0)
    new_restaurants = models.PositiveIntegerField(_('Nouveaux restaurants'), default=0)
    new_delivery_persons = models.PositiveIntegerField(_('Nouveaux livreurs'), default=0)
    active_customers = models.PositiveIntegerField(_('Clients actifs'), default=0)
    
    # Livraisons
    total_deliveries = models.PositiveIntegerField(_('Livraisons totales'), default=0)
    successful_deliveries = models.PositiveIntegerField(_('Livraisons réussies'), default=0)
    average_delivery_time = models.DecimalField(
        _('Temps de livraison moyen (minutes)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    
    # Évaluations
    total_reviews = models.PositiveIntegerField(_('Avis totaux'), default=0)
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Statistiques quotidiennes')
        verbose_name_plural = _('Statistiques quotidiennes')
        ordering = ['-date']
        
    def __str__(self):
        return f"Stats {self.date} - {self.total_orders} commandes"


class RestaurantStats(models.Model):
    """
    Statistiques spécifiques aux restaurants.
    """
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='stats'
    )
    date = models.DateField(_('Date'))
    
    # Commandes
    total_orders = models.PositiveIntegerField(_('Commandes totales'), default=0)
    completed_orders = models.PositiveIntegerField(_('Commandes terminées'), default=0)
    cancelled_orders = models.PositiveIntegerField(_('Commandes annulées'), default=0)
    
    # Revenus
    gross_revenue = models.DecimalField(
        _('Revenus bruts'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    net_revenue = models.DecimalField(
        _('Revenus nets'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    platform_fees = models.DecimalField(
        _('Frais plateforme'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Performance
    average_order_value = models.DecimalField(
        _('Valeur moyenne des commandes'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    average_preparation_time = models.DecimalField(
        _('Temps de préparation moyen (minutes)'),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    
    # Évaluations
    new_reviews = models.PositiveIntegerField(_('Nouveaux avis'), default=0)
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    # Clients
    unique_customers = models.PositiveIntegerField(_('Clients uniques'), default=0)
    returning_customers = models.PositiveIntegerField(_('Clients de retour'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Statistiques de restaurant')
        verbose_name_plural = _('Statistiques de restaurants')
        unique_together = ['restaurant', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.restaurant.name} - {self.date}"


class MenuItemStats(models.Model):
    """
    Statistiques des éléments de menu.
    """
    menu_item = models.ForeignKey(
        'restaurants.MenuItem',
        on_delete=models.CASCADE,
        related_name='stats'
    )
    date = models.DateField(_('Date'))
    
    # Ventes
    total_ordered = models.PositiveIntegerField(_('Quantité commandée'), default=0)
    total_revenue = models.DecimalField(
        _('Revenus générés'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Performance
    views = models.PositiveIntegerField(_('Vues'), default=0)
    add_to_cart = models.PositiveIntegerField(_('Ajouts au panier'), default=0)
    conversion_rate = models.DecimalField(
        _('Taux de conversion (%)'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Évaluations
    new_reviews = models.PositiveIntegerField(_('Nouveaux avis'), default=0)
    average_rating = models.DecimalField(
        _('Note moyenne'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Statistiques d\'élément de menu')
        verbose_name_plural = _('Statistiques d\'éléments de menu')
        unique_together = ['menu_item', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.menu_item.name} - {self.date}"


class UserBehavior(models.Model):
    """
    Suivi du comportement des utilisateurs.
    """
    ACTION_CHOICES = [
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('view_restaurant', _('Vue restaurant')),
        ('view_menu_item', _('Vue élément menu')),
        ('add_to_cart', _('Ajout au panier')),
        ('remove_from_cart', _('Retrait du panier')),
        ('place_order', _('Passer commande')),
        ('cancel_order', _('Annuler commande')),
        ('rate_restaurant', _('Noter restaurant')),
        ('rate_delivery', _('Noter livraison')),
        ('use_coupon', _('Utiliser coupon')),
        ('redeem_points', _('Échanger points')),
        ('search', _('Recherche')),
        ('filter', _('Filtrer')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='behavior_logs'
    )
    
    # Action
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    
    # Contexte
    context_data = models.JSONField(
        _('Données de contexte'),
        default=dict,
        blank=True
    )
    
    # Références
    related_restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_interactions'
    )
    related_menu_item = models.ForeignKey(
        'restaurants.MenuItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_interactions'
    )
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_interactions'
    )
    
    # Informations techniques
    ip_address = models.GenericIPAddressField(_('Adresse IP'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    session_id = models.CharField(_('ID de session'), max_length=100, blank=True)
    
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
    timestamp = models.DateTimeField(_('Horodatage'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Comportement utilisateur')
        verbose_name_plural = _('Comportements utilisateurs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} ({self.timestamp})"


class SearchQuery(models.Model):
    """
    Requêtes de recherche des utilisateurs.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries'
    )
    
    # Requête
    query = models.CharField(_('Requête'), max_length=500)
    filters_applied = models.JSONField(
        _('Filtres appliqués'),
        default=dict,
        blank=True
    )
    
    # Résultats
    results_count = models.PositiveIntegerField(_('Nombre de résultats'), default=0)
    clicked_restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_clicks'
    )
    
    # Géolocalisation
    search_latitude = models.DecimalField(
        _('Latitude de recherche'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    search_longitude = models.DecimalField(
        _('Longitude de recherche'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Informations techniques
    ip_address = models.GenericIPAddressField(_('Adresse IP'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    # Métadonnées
    searched_at = models.DateTimeField(_('Recherché le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Requête de recherche')
        verbose_name_plural = _('Requêtes de recherche')
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['query', '-searched_at']),
        ]
        
    def __str__(self):
        return f"Recherche: '{self.query}' ({self.results_count} résultats)"


class PerformanceMetric(models.Model):
    """
    Métriques de performance de l'application.
    """
    METRIC_TYPE_CHOICES = [
        ('response_time', _('Temps de réponse')),
        ('page_load_time', _('Temps de chargement de page')),
        ('api_response_time', _('Temps de réponse API')),
        ('database_query_time', _('Temps de requête DB')),
        ('error_rate', _('Taux d\'erreur')),
        ('uptime', _('Temps de fonctionnement')),
    ]
    
    # Type et identification
    metric_type = models.CharField(_('Type de métrique'), max_length=30, choices=METRIC_TYPE_CHOICES)
    endpoint = models.CharField(_('Endpoint'), max_length=200, blank=True)
    
    # Valeurs
    value = models.DecimalField(
        _('Valeur'),
        max_digits=10,
        decimal_places=3
    )
    unit = models.CharField(_('Unité'), max_length=20, default='ms')
    
    # Contexte
    context_data = models.JSONField(
        _('Données de contexte'),
        default=dict,
        blank=True
    )
    
    # Métadonnées
    recorded_at = models.DateTimeField(_('Enregistré le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Métrique de performance')
        verbose_name_plural = _('Métriques de performance')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', '-recorded_at']),
            models.Index(fields=['endpoint', '-recorded_at']),
        ]
        
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} {self.unit}"


class ConversionFunnel(models.Model):
    """
    Analyse du funnel de conversion.
    """
    STEP_CHOICES = [
        ('landing', _('Page d\'accueil')),
        ('restaurant_list', _('Liste restaurants')),
        ('restaurant_detail', _('Détail restaurant')),
        ('menu_view', _('Vue menu')),
        ('add_to_cart', _('Ajout au panier')),
        ('cart_view', _('Vue panier')),
        ('checkout_start', _('Début commande')),
        ('payment_start', _('Début paiement')),
        ('order_completed', _('Commande terminée')),
    ]
    
    date = models.DateField(_('Date'))
    step = models.CharField(_('Étape'), max_length=20, choices=STEP_CHOICES)
    
    # Métriques
    unique_users = models.PositiveIntegerField(_('Utilisateurs uniques'), default=0)
    total_sessions = models.PositiveIntegerField(_('Sessions totales'), default=0)
    conversions = models.PositiveIntegerField(_('Conversions'), default=0)
    
    # Taux de conversion
    conversion_rate = models.DecimalField(
        _('Taux de conversion (%)'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Segmentation
    user_type = models.CharField(_('Type d\'utilisateur'), max_length=20, blank=True)
    device_type = models.CharField(_('Type d\'appareil'), max_length=20, blank=True)
    traffic_source = models.CharField(_('Source de trafic'), max_length=50, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Funnel de conversion')
        verbose_name_plural = _('Funnels de conversion')
        unique_together = ['date', 'step', 'user_type', 'device_type']
        ordering = ['-date', 'step']
        
    def __str__(self):
        return f"{self.date} - {self.get_step_display()}: {self.conversion_rate}%"


class RevenueReport(models.Model):
    """
    Rapports de revenus détaillés.
    """
    PERIOD_CHOICES = [
        ('daily', _('Quotidien')),
        ('weekly', _('Hebdomadaire')),
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
    ]
    
    # Période
    period_type = models.CharField(_('Type de période'), max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField(_('Date de début'))
    end_date = models.DateField(_('Date de fin'))
    
    # Restaurant spécifique (optionnel)
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='revenue_reports'
    )
    
    # Revenus
    gross_revenue = models.DecimalField(
        _('Revenus bruts'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    net_revenue = models.DecimalField(
        _('Revenus nets'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    platform_commission = models.DecimalField(
        _('Commission plateforme'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    delivery_fees = models.DecimalField(
        _('Frais de livraison'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    taxes = models.DecimalField(
        _('Taxes'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Répartition par méthode de paiement
    stripe_revenue = models.DecimalField(_('Revenus Stripe'), max_digits=10, decimal_places=2, default=0)
    tmoney_revenue = models.DecimalField(_('Revenus Tmoney'), max_digits=10, decimal_places=2, default=0)
    flooz_revenue = models.DecimalField(_('Revenus Flooz'), max_digits=10, decimal_places=2, default=0)
    cash_revenue = models.DecimalField(_('Revenus espèces'), max_digits=10, decimal_places=2, default=0)
    wallet_revenue = models.DecimalField(_('Revenus portefeuille'), max_digits=10, decimal_places=2, default=0)
    
    # Métriques
    total_orders = models.PositiveIntegerField(_('Commandes totales'), default=0)
    average_order_value = models.DecimalField(
        _('Valeur moyenne des commandes'),
        max_digits=8,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    generated_at = models.DateTimeField(_('Généré le'), auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )
    
    class Meta:
        verbose_name = _('Rapport de revenus')
        verbose_name_plural = _('Rapports de revenus')
        ordering = ['-start_date']
        
    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else "Global"
        return f"Rapport {restaurant_name} - {self.start_date} à {self.end_date}"


class PopularityIndex(models.Model):
    """
    Index de popularité des restaurants et plats.
    """
    ENTITY_TYPE_CHOICES = [
        ('restaurant', _('Restaurant')),
        ('menu_item', _('Élément de menu')),
        ('category', _('Catégorie')),
    ]
    
    # Type d'entité
    entity_type = models.CharField(_('Type d\'entité'), max_length=20, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.PositiveIntegerField(_('ID de l\'entité'))
    
    # Scores de popularité
    view_score = models.DecimalField(
        _('Score de vues'),
        max_digits=10,
        decimal_places=3,
        default=0
    )
    order_score = models.DecimalField(
        _('Score de commandes'),
        max_digits=10,
        decimal_places=3,
        default=0
    )
    rating_score = models.DecimalField(
        _('Score d\'évaluation'),
        max_digits=10,
        decimal_places=3,
        default=0
    )
    overall_score = models.DecimalField(
        _('Score global'),
        max_digits=10,
        decimal_places=3,
        default=0
    )
    
    # Période de calcul
    calculation_date = models.DateField(_('Date de calcul'))
    
    # Rang
    rank = models.PositiveIntegerField(_('Rang'), default=0)
    previous_rank = models.PositiveIntegerField(_('Rang précédent'), default=0)
    
    # Métadonnées
    calculated_at = models.DateTimeField(_('Calculé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Index de popularité')
        verbose_name_plural = _('Index de popularité')
        unique_together = ['entity_type', 'entity_id', 'calculation_date']
        ordering = ['-overall_score']
        
    def __str__(self):
        return f"{self.get_entity_type_display()} {self.entity_id} - Score: {self.overall_score}"
    
    def get_rank_change(self):
        """Calcule le changement de rang."""
        if self.previous_rank == 0:
            return 0
        return self.previous_rank - self.rank


class CustomerSegment(models.Model):
    """
    Segmentation des clients pour analytics.
    """
    SEGMENT_TYPE_CHOICES = [
        ('high_value', _('Haute valeur')),
        ('frequent', _('Fréquent')),
        ('occasional', _('Occasionnel')),
        ('new', _('Nouveau')),
        ('churned', _('Perdu')),
        ('at_risk', _('À risque')),
    ]
    
    name = models.CharField(_('Nom du segment'), max_length=100)
    segment_type = models.CharField(_('Type de segment'), max_length=20, choices=SEGMENT_TYPE_CHOICES)
    description = models.TextField(_('Description'), blank=True)
    
    # Critères de segmentation
    criteria = models.JSONField(
        _('Critères'),
        default=dict,
        help_text=_('Critères pour appartenir à ce segment')
    )
    
    # Utilisateurs dans le segment
    users = models.ManyToManyField(
        User,
        through='CustomerSegmentMembership',
        related_name='segments'
    )
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_calculated = models.DateTimeField(_('Dernière mise à jour'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Segment de clients')
        verbose_name_plural = _('Segments de clients')
        ordering = ['name']
        
    def __str__(self):
        return self.name


class CustomerSegmentMembership(models.Model):
    """
    Appartenance des clients aux segments.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='segment_memberships'
    )
    segment = models.ForeignKey(
        CustomerSegment,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    
    # Score d'appartenance
    score = models.DecimalField(
        _('Score d\'appartenance'),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    joined_at = models.DateTimeField(_('Rejoint le'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Dernière mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('Appartenance au segment')
        verbose_name_plural = _('Appartenances aux segments')
        unique_together = ['user', 'segment']
        ordering = ['-score']
        
    def __str__(self):
        return f"{self.user.email} → {self.segment.name} (Score: {self.score})"
