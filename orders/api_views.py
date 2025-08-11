"""
ViewSets pour l'API REST de l'application orders.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem, Cart, CartItem, Coupon, OrderTracking
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer,
    CartSerializer, CartItemCreateSerializer, CouponSerializer,
    OrderTrackingSerializer, OrderStatusUpdateSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des commandes.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur."""
        user = self.request.user
        
        if user.user_type == 'client':
            return Order.objects.filter(customer=user)
        elif user.user_type == 'restaurant':
            # Commandes pour les restaurants de l'utilisateur
            return Order.objects.filter(restaurant__owner=user)
        elif user.user_type == 'delivery':
            # Commandes assignées au livreur
            return Order.objects.filter(delivery_assignment__delivery_person__user=user)
        elif user.is_staff:
            return Order.objects.all()
        
        return Order.objects.none()
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action."""
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        """Mettre à jour le statut d'une commande."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data, context={'order': order})
        
        if serializer.is_valid():
            # Vérifier les permissions
            if (order.restaurant.owner != request.user and 
                not request.user.is_staff and
                request.user.user_type != 'delivery'):
                return Response({
                    'error': _('Permission refusée.')
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Mettre à jour le statut
            order.status = serializer.validated_data['status']
            if 'estimated_delivery_time' in serializer.validated_data:
                order.estimated_delivery_time = serializer.validated_data['estimated_delivery_time']
            order.save()
            
            # Créer un enregistrement de suivi
            OrderTracking.objects.create(
                order=order,
                status=order.status,
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'message': _('Statut mis à jour avec succès.'),
                'order': OrderSerializer(order).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        """Suivi d'une commande."""
        order = self.get_object()
        tracking = OrderTracking.objects.filter(order=order).order_by('timestamp')
        serializer = OrderTrackingSerializer(tracking, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler une commande."""
        order = self.get_object()
        
        # Vérifier si l'annulation est possible
        if order.status not in ['pending', 'confirmed']:
            return Response({
                'error': _('Cette commande ne peut plus être annulée.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'cancelled'
        order.save()
        
        return Response({
            'message': _('Commande annulée avec succès.')
        }, status=status.HTTP_200_OK)


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion du panier.
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur."""
        return Cart.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Obtenir ou créer le panier de l'utilisateur."""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Ajouter un article au panier."""
        cart = self.get_object()
        serializer = CartItemCreateSerializer(data=request.data, context={'cart': cart})
        
        if serializer.is_valid():
            cart_item = serializer.save()
            return Response({
                'message': _('Article ajouté au panier.'),
                'cart_item': CartItemSerializer(cart_item).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['put'])
    def update_item(self, request):
        """Mettre à jour un article du panier."""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            quantity = request.data.get('quantity', cart_item.quantity)
            
            if quantity <= 0:
                cart_item.delete()
                return Response({
                    'message': _('Article supprimé du panier.')
                }, status=status.HTTP_200_OK)
            else:
                cart_item.quantity = quantity
                cart_item.save()
                return Response({
                    'message': _('Panier mis à jour.'),
                    'cart_item': CartItemSerializer(cart_item).data
                }, status=status.HTTP_200_OK)
        
        except CartItem.DoesNotExist:
            return Response({
                'error': _('Article non trouvé dans le panier.')
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Supprimer un article du panier."""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response({
                'message': _('Article supprimé du panier.')
            }, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({
                'error': _('Article non trouvé dans le panier.')
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Vider le panier."""
        cart = self.get_object()
        CartItem.objects.filter(cart=cart).delete()
        return Response({
            'message': _('Panier vidé.')
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Finaliser la commande depuis le panier."""
        cart = self.get_object()
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return Response({
                'error': _('Le panier est vide.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la commande
        order_data = {
            'restaurant': cart_items.first().menu_item.restaurant.id,
            'delivery_address': request.data.get('delivery_address'),
            'delivery_phone': request.data.get('delivery_phone'),
            'special_instructions': request.data.get('special_instructions', ''),
            'payment_method': request.data.get('payment_method', 'cash'),
            'items': [
                {
                    'menu_item_id': item.menu_item.id,
                    'quantity': item.quantity,
                    'customizations': item.customizations,
                    'special_instructions': item.special_instructions
                }
                for item in cart_items
            ]
        }
        
        order_serializer = OrderCreateSerializer(data=order_data, context={'request': request})
        if order_serializer.is_valid():
            order = order_serializer.save()
            
            # Vider le panier
            cart_items.delete()
            
            return Response({
                'message': _('Commande créée avec succès.'),
                'order': OrderSerializer(order).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les coupons (lecture seule).
    """
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def validate_coupon(self, request):
        """Valider un code de coupon."""
        code = request.data.get('code')
        order_amount = request.data.get('order_amount', 0)
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            
            if coupon.is_valid() and order_amount >= coupon.minimum_order:
                return Response({
                    'valid': True,
                    'coupon': CouponSerializer(coupon).data,
                    'discount_amount': coupon.calculate_discount(order_amount)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'valid': False,
                    'error': _('Coupon invalide ou montant minimum non atteint.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': _('Code de coupon invalide.')
            }, status=status.HTTP_404_NOT_FOUND)