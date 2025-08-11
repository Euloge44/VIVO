"""
Serializers pour l'application restaurants.
"""

from rest_framework import serializers
from .models import Restaurant, MenuItem, Category, RestaurantImage, SpecialOffer
from accounts.serializers import CustomUserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer pour les catégories.
    """
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'is_active', 'order', 'children']
    
    def get_children(self, obj):
        """Obtenir les sous-catégories."""
        children = obj.get_children().filter(is_active=True)
        return CategorySerializer(children, many=True).data


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer pour les articles du menu.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_name',
            'restaurant', 'restaurant_name', 'image', 'preparation_time',
            'calories', 'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'is_spicy', 'spice_level', 'allergens', 'nutritional_info',
            'is_available', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'category_name', 'restaurant_name']


class RestaurantImageSerializer(serializers.ModelSerializer):
    """
    Serializer pour les images de restaurant.
    """
    class Meta:
        model = RestaurantImage
        fields = ['id', 'image', 'alt_text', 'is_main', 'order']


class SpecialOfferSerializer(serializers.ModelSerializer):
    """
    Serializer pour les offres spéciales.
    """
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = SpecialOffer
        fields = [
            'id', 'restaurant', 'restaurant_name', 'title', 'description',
            'discount_type', 'discount_value', 'minimum_order', 'valid_from',
            'valid_until', 'is_active', 'max_uses', 'current_uses'
        ]


class RestaurantSerializer(serializers.ModelSerializer):
    """
    Serializer pour les restaurants.
    """
    owner = CustomUserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    images = RestaurantImageSerializer(many=True, read_only=True)
    special_offers = SpecialOfferSerializer(many=True, read_only=True)
    distance = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    menu_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'owner', 'name', 'description', 'address', 'city', 'postal_code',
            'phone', 'email', 'website', 'logo', 'cover_image', 'latitude',
            'longitude', 'categories', 'cuisine_type', 'price_range',
            'opening_hours', 'delivery_fee', 'minimum_order', 'estimated_delivery_time',
            'average_rating', 'total_reviews', 'is_active', 'is_featured',
            'accepts_cash', 'accepts_card', 'accepts_mobile_payment',
            'images', 'special_offers', 'distance', 'is_open', 'menu_items_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'average_rating', 'total_reviews', 'distance',
            'is_open', 'menu_items_count', 'created_at', 'updated_at'
        ]
    
    def get_distance(self, obj):
        """Calculer la distance depuis la position de l'utilisateur."""
        # À implémenter avec la géolocalisation
        return None
    
    def get_is_open(self, obj):
        """Vérifier si le restaurant est ouvert."""
        return obj.is_open_now()
    
    def get_menu_items_count(self, obj):
        """Compter les articles du menu disponibles."""
        return obj.menu_items.filter(is_available=True).count()


class RestaurantListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la liste des restaurants.
    """
    distance = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 'address', 'phone', 'logo',
            'cover_image', 'cuisine_type', 'price_range', 'delivery_fee',
            'minimum_order', 'estimated_delivery_time', 'average_rating',
            'total_reviews', 'is_featured', 'distance', 'is_open'
        ]
    
    def get_distance(self, obj):
        """Calculer la distance depuis la position de l'utilisateur."""
        # À implémenter avec la géolocalisation
        return None
    
    def get_is_open(self, obj):
        """Vérifier si le restaurant est ouvert."""
        return obj.is_open_now()


class RestaurantCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'un restaurant.
    """
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'address', 'city', 'postal_code',
            'phone', 'email', 'website', 'cuisine_type', 'price_range',
            'opening_hours', 'delivery_fee', 'minimum_order',
            'estimated_delivery_time', 'accepts_cash', 'accepts_card',
            'accepts_mobile_payment'
        ]
    
    def create(self, validated_data):
        """Créer un nouveau restaurant."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'articles de menu.
    """
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'price', 'category', 'preparation_time',
            'calories', 'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'is_spicy', 'spice_level', 'allergens', 'nutritional_info',
            'is_available', 'order'
        ]
    
    def create(self, validated_data):
        """Créer un nouvel article de menu."""
        # Le restaurant sera défini dans la vue
        return super().create(validated_data)


class RestaurantStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques de restaurant.
    """
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    popular_items = serializers.ListField()
    orders_today = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()


class RestaurantSearchSerializer(serializers.Serializer):
    """
    Serializer pour la recherche de restaurants.
    """
    query = serializers.CharField(max_length=200, required=False)
    category = serializers.CharField(max_length=100, required=False)
    cuisine_type = serializers.CharField(max_length=100, required=False)
    price_range = serializers.CharField(max_length=20, required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    radius = serializers.FloatField(required=False, default=5.0)
    is_open = serializers.BooleanField(required=False)
    min_rating = serializers.FloatField(required=False, min_value=0, max_value=5)
    delivery_fee_max = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    minimum_order_max = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)