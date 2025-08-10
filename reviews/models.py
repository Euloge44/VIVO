"""
Modèles pour le système d'évaluations et d'avis de GourmetGuide.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Review(models.Model):
    """
    Avis et évaluations des restaurants.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente de modération')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('hidden', _('Masqué')),
    ]
    
    # Relations
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        limit_choices_to={'user_type': 'client'}
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='review',
        blank=True,
        null=True
    )
    
    # Évaluations détaillées
    overall_rating = models.PositiveIntegerField(
        _('Note globale'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    food_quality_rating = models.PositiveIntegerField(
        _('Qualité de la nourriture'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    service_rating = models.PositiveIntegerField(
        _('Service'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    delivery_rating = models.PositiveIntegerField(
        _('Livraison'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    value_rating = models.PositiveIntegerField(
        _('Rapport qualité/prix'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Contenu de l'avis
    title = models.CharField(_('Titre'), max_length=200, blank=True)
    comment = models.TextField(_('Commentaire'), blank=True)
    
    # Images de l'avis
    images = models.JSONField(
        _('Images'),
        default=list,
        blank=True,
        help_text=_('URLs des images uploadées')
    )
    
    # Statut et modération
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews',
        limit_choices_to={'user_type': 'admin'}
    )
    moderation_notes = models.TextField(_('Notes de modération'), blank=True)
    
    # Interaction
    helpful_count = models.PositiveIntegerField(_('Nombre de "utile"'), default=0)
    reported_count = models.PositiveIntegerField(_('Nombre de signalements'), default=0)
    
    # Réponse du restaurant
    restaurant_response = models.TextField(_('Réponse du restaurant'), blank=True)
    restaurant_response_date = models.DateTimeField(_('Date de réponse'), blank=True, null=True)
    restaurant_responder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_responses'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Avis')
        verbose_name_plural = _('Avis')
        unique_together = ['customer', 'restaurant', 'order']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Avis de {self.customer.email} sur {self.restaurant.name} ({self.overall_rating}/5)"
    
    def get_average_rating(self):
        """Calcule la note moyenne de tous les critères."""
        ratings = [self.overall_rating, self.food_quality_rating, self.service_rating, self.value_rating]
        if self.delivery_rating:
            ratings.append(self.delivery_rating)
        return sum(ratings) / len(ratings)
    
    def can_be_edited(self):
        """Vérifie si l'avis peut être modifié."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Peut être édité dans les 24h après création
        edit_deadline = self.created_at + timedelta(hours=24)
        return timezone.now() < edit_deadline and self.status == 'pending'


class MenuItemReview(models.Model):
    """
    Avis spécifiques aux éléments du menu.
    """
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='menu_reviews_given',
        limit_choices_to={'user_type': 'client'}
    )
    menu_item = models.ForeignKey(
        'restaurants.MenuItem',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    order_item = models.OneToOneField(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        related_name='review',
        blank=True,
        null=True
    )
    
    # Évaluations
    rating = models.PositiveIntegerField(
        _('Note'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    taste_rating = models.PositiveIntegerField(
        _('Goût'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    presentation_rating = models.PositiveIntegerField(
        _('Présentation'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    portion_rating = models.PositiveIntegerField(
        _('Portion'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Commentaire
    comment = models.TextField(_('Commentaire'), blank=True)
    
    # Tags descriptifs
    taste_tags = models.JSONField(
        _('Tags de goût'),
        default=list,
        blank=True,
        help_text=_('Tags : délicieux, épicé, salé, sucré, etc.')
    )
    
    # Recommandation
    would_recommend = models.BooleanField(_('Recommanderait'), default=True)
    
    # Statut
    is_verified_purchase = models.BooleanField(_('Achat vérifié'), default=False)
    is_approved = models.BooleanField(_('Approuvé'), default=True)
    
    # Interaction
    helpful_count = models.PositiveIntegerField(_('Nombre de "utile"'), default=0)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Avis de plat')
        verbose_name_plural = _('Avis de plats')
        unique_together = ['customer', 'menu_item', 'order_item']
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Avis de {self.customer.email} sur {self.menu_item.name} ({self.rating}/5)"


class ReviewHelpful(models.Model):
    """
    Votes "utile" sur les avis.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    
    is_helpful = models.BooleanField(_('Utile'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vote utile')
        verbose_name_plural = _('Votes utiles')
        unique_together = ['user', 'review']
        
    def __str__(self):
        return f"{self.user.email} trouve l'avis {'utile' if self.is_helpful else 'pas utile'}"


class ReviewReport(models.Model):
    """
    Signalements d'avis inappropriés.
    """
    REASON_CHOICES = [
        ('spam', _('Spam')),
        ('fake', _('Faux avis')),
        ('inappropriate', _('Contenu inapproprié')),
        ('offensive', _('Contenu offensant')),
        ('irrelevant', _('Hors sujet')),
        ('personal_attack', _('Attaque personnelle')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('reviewing', _('En cours d\'examen')),
        ('resolved', _('Résolu')),
        ('dismissed', _('Rejeté')),
    ]
    
    # Relations
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_reports_made'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    # Détails du signalement
    reason = models.CharField(_('Raison'), max_length=20, choices=REASON_CHOICES)
    description = models.TextField(_('Description'), blank=True)
    
    # Traitement
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review_reports_handled',
        limit_choices_to={'user_type': 'admin'}
    )
    admin_notes = models.TextField(_('Notes admin'), blank=True)
    
    # Métadonnées
    reported_at = models.DateTimeField(_('Signalé le'), auto_now_add=True)
    resolved_at = models.DateTimeField(_('Résolu le'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Signalement d\'avis')
        verbose_name_plural = _('Signalements d\'avis')
        unique_together = ['reporter', 'review']
        ordering = ['-reported_at']
        
    def __str__(self):
        return f"Signalement: {self.get_reason_display()} - Avis {self.review.id}"


class ReviewImage(models.Model):
    """
    Images associées aux avis.
    """
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='review_images'
    )
    
    image = models.CharField(_('Image'), max_length=255, blank=True)
    caption = models.CharField(_('Légende'), max_length=200, blank=True)
    
    # Métadonnées
    uploaded_at = models.DateTimeField(_('Uploadé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Image d\'avis')
        verbose_name_plural = _('Images d\'avis')
        ordering = ['uploaded_at']
        
    def __str__(self):
        return f"Image pour avis {self.review.id}"


class ReviewTemplate(models.Model):
    """
    Templates d'avis prédéfinis pour faciliter la saisie.
    """
    CATEGORY_CHOICES = [
        ('positive', _('Positif')),
        ('negative', _('Négatif')),
        ('neutral', _('Neutre')),
    ]
    
    category = models.CharField(_('Catégorie'), max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(_('Titre'), max_length=200)
    content = models.TextField(_('Contenu'))
    
    # Critères suggérés
    suggested_overall_rating = models.PositiveIntegerField(
        _('Note globale suggérée'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Usage
    usage_count = models.PositiveIntegerField(_('Nombre d\'utilisations'), default=0)
    
    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('Template d\'avis')
        verbose_name_plural = _('Templates d\'avis')
        ordering = ['category', '-usage_count']
        
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
