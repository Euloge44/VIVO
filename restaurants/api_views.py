"""
ViewSets pour l'API REST de l'application restaurants.
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from django.utils.translation import gettext_lazy as _
from .models import Restaurant, MenuItem, Category, SpecialOffer
from .serializers import (
    RestaurantSerializer, RestaurantListSerializer, RestaurantCreateSerializer,
    MenuItemSerializer, MenuItemCreateSerializer, CategorySerializer,
    SpecialOfferSerializer, RestaurantStatsSerializer, RestaurantSearchSerializer
)


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des restaurants.
    """
    queryset = Restaurant.objects.filter(status='active')
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured', 'is_verified']
    search_fields = ['name', 'description', 'address', 'city']
    ordering_fields = ['name', 'average_rating', 'created_at']
    ordering = ['-average_rating', 'name']
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action."""
        if self.action == 'list':
            return RestaurantListSerializer
        elif self.action == 'create':
            return RestaurantCreateSerializer
        return RestaurantSerializer
    
    def get_queryset(self):
        """Filtrer selon les permissions et paramètres."""
        queryset = Restaurant.objects.filter(status='active')
        
        # Filtres géographiques
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius', 5)
        
        if latitude and longitude:
            # À implémenter avec la géolocalisation
            pass
        
        # Filtre par statut ouvert
        is_open = self.request.query_params.get('is_open')
        if is_open == 'true':
            # À implémenter avec les heures d'ouverture
            pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Assigner le propriétaire lors de la création."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def menu(self, request, pk=None):
        """Menu du restaurant."""
        restaurant = self.get_object()
        menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
        serializer = MenuItemSerializer(menu_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Statistiques du restaurant."""
        restaurant = self.get_object()
        
        # Vérifier que l'utilisateur est le propriétaire
        if restaurant.owner != request.user and not request.user.is_staff:
            return Response({
                'error': _('Permission refusée.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calculer les statistiques
        stats = {
            'total_orders': 0,  # À implémenter
            'total_revenue': 0,  # À implémenter
            'average_rating': restaurant.average_rating,
            'total_reviews': restaurant.total_reviews,
            'popular_items': [],  # À implémenter
            'orders_today': 0,  # À implémenter
            'revenue_today': 0,  # À implémenter
            'pending_orders': 0,  # À implémenter
        }
        
        serializer = RestaurantStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Recherche avancée de restaurants."""
        serializer = RestaurantSearchSerializer(data=request.data)
        if serializer.is_valid():
            # Implémenter la logique de recherche
            queryset = self.get_queryset()
            
            query = serializer.validated_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(cuisine_type__icontains=query)
                )
            
            # Autres filtres...
            
            serializer = RestaurantListSerializer(queryset, many=True)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des articles de menu.
    """
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy']
    search_fields = ['name', 'description', 'allergens']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action."""
        if self.action == 'create':
            return MenuItemCreateSerializer
        return MenuItemSerializer
    
    def get_queryset(self):
        """Filtrer selon le restaurant."""
        queryset = MenuItem.objects.filter(is_available=True)
        
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Assigner le restaurant lors de la création."""
        restaurant_id = self.request.data.get('restaurant_id')
        if restaurant_id:
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id, owner=self.request.user)
                serializer.save(restaurant=restaurant)
            except Restaurant.DoesNotExist:
                raise permissions.PermissionDenied(_('Restaurant non trouvé ou non autorisé.'))


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les catégories (lecture seule).
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering = ['order', 'name']
    
    @action(detail=True, methods=['get'])
    def restaurants(self, request, pk=None):
        """Restaurants d'une catégorie."""
        category = self.get_object()
        restaurants = Restaurant.objects.filter(categories=category, status='active')
        serializer = RestaurantListSerializer(restaurants, many=True)
        return Response(serializer.data)


class SpecialOfferViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les offres spéciales (lecture seule).
    """
    queryset = SpecialOffer.objects.filter(is_active=True)
    serializer_class = SpecialOfferSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['restaurant', 'discount_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les offres valides."""
        from django.utils import timezone
        now = timezone.now()
        
        return SpecialOffer.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )