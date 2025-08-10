"""
Serializers pour l'application orders.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, Cart, CartItem, Coupon, OrderTracking
from restaurants.serializers import MenuItemSerializer, RestaurantListSerializer
from accounts.serializers import CustomUserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer pour les articles d'une commande.
    """
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'quantity', 'unit_price', 'customizations',
            'special_instructions', 'total_price'
        ]
    
    def get_total_price(self, obj):
        """Calculer le prix total de l'article."""
        return obj.get_total_price()


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer pour les commandes.
    """
    customer = CustomUserSerializer(read_only=True)
    restaurant = RestaurantListSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'restaurant', 'items', 'status', 'status_display',
            'subtotal', 'delivery_fee', 'tax_amount', 'discount_amount',
            'total_amount', 'payment_method', 'delivery_address', 'delivery_phone',
            'special_instructions', 'estimated_delivery_time', 'actual_delivery_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'customer', 'subtotal', 'tax_amount', 'total_amount',
            'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'une commande.
    """
    items = serializers.ListField(write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'restaurant', 'delivery_address', 'delivery_phone',
            'special_instructions', 'payment_method', 'items'
        ]
    
    def validate_items(self, value):
        """Valider les articles de la commande."""
        if not value:
            raise serializers.ValidationError("Au moins un article est requis.")
        
        for item in value:
            if 'menu_item_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Chaque article doit avoir menu_item_id et quantity.")
            
            if item['quantity'] <= 0:
                raise serializers.ValidationError("La quantité doit être positive.")
        
        return value
    
    def create(self, validated_data):
        """Créer une nouvelle commande."""
        items_data = validated_data.pop('items')
        validated_data['customer'] = self.context['request'].user
        
        order = Order.objects.create(**validated_data)
        
        # Créer les articles de la commande
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                menu_item_id=item_data['menu_item_id'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price', 0),
                customizations=item_data.get('customizations', {}),
                special_instructions=item_data.get('special_instructions', '')
            )
        
        # Recalculer le total
        order.calculate_total()
        
        return order


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer pour les articles du panier.
    """
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'menu_item', 'quantity', 'customizations',
            'special_instructions', 'total_price', 'added_at'
        ]
    
    def get_total_price(self, obj):
        """Calculer le prix total de l'article."""
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer pour le panier.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'total_items', 'total_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_total_items(self, obj):
        """Compter le nombre total d'articles."""
        return sum(item.quantity for item in obj.items.all())
    
    def get_total_amount(self, obj):
        """Calculer le montant total du panier."""
        return sum(item.get_total_price() for item in obj.items.all())


class CartItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour ajouter un article au panier.
    """
    menu_item_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'menu_item_id', 'quantity', 'customizations', 'special_instructions'
        ]
    
    def validate_quantity(self, value):
        """Valider la quantité."""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive.")
        if value > 50:
            raise serializers.ValidationError("Quantité maximale: 50.")
        return value
    
    def create(self, validated_data):
        """Créer ou mettre à jour un article du panier."""
        menu_item_id = validated_data.pop('menu_item_id')
        cart = self.context['cart']
        
        # Vérifier si l'article existe déjà
        try:
            cart_item = CartItem.objects.get(cart=cart, menu_item_id=menu_item_id)
            cart_item.quantity += validated_data['quantity']
            cart_item.customizations = validated_data.get('customizations', {})
            cart_item.special_instructions = validated_data.get('special_instructions', '')
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(
                cart=cart,
                menu_item_id=menu_item_id,
                **validated_data
            )
        
        return cart_item


class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer pour les coupons.
    """
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'minimum_order',
            'valid_from', 'valid_until', 'max_uses', 'current_uses',
            'is_active', 'is_valid'
        ]
    
    def get_is_valid(self, obj):
        """Vérifier si le coupon est valide."""
        return obj.is_valid()


class OrderTrackingSerializer(serializers.ModelSerializer):
    """
    Serializer pour le suivi de commande.
    """
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'order', 'status', 'location_latitude', 'location_longitude',
            'estimated_arrival', 'notes', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer pour la mise à jour du statut de commande.
    """
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    notes = serializers.CharField(max_length=500, required=False)
    estimated_delivery_time = serializers.DateTimeField(required=False)
    
    def validate_status(self, value):
        """Valider la transition de statut."""
        order = self.context.get('order')
        if order:
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['preparing', 'cancelled'],
                'preparing': ['ready', 'cancelled'],
                'ready': ['picked_up'],
                'picked_up': ['delivered'],
                'delivered': [],
                'cancelled': []
            }
            
            if value not in valid_transitions.get(order.status, []):
                raise serializers.ValidationError(
                    f"Transition invalide de {order.status} vers {value}"
                )
        
        return value