"""
Vues pour l'application orders.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Order, Cart, CartItem


class OrderListView(LoginRequiredMixin, ListView):
    """Liste des commandes de l'utilisateur."""
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une commande."""
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class OrderCreateView(LoginRequiredMixin, View):
    """Création d'une commande."""
    def post(self, request):
        # Logique de création de commande à implémenter
        messages.success(request, _('Commande créée avec succès'))
        return redirect('orders:list')


class OrderTrackingView(LoginRequiredMixin, DetailView):
    """Suivi d'une commande."""
    model = Order
    template_name = 'orders/tracking.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class CartView(LoginRequiredMixin, View):
    """Panier de l'utilisateur."""
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
            'total': sum(item.get_total_price() for item in cart_items)
        }
        return render(request, 'orders/cart.html', context)


class AddToCartView(LoginRequiredMixin, View):
    """Ajouter un article au panier."""
    def post(self, request):
        # Logique d'ajout au panier à implémenter
        messages.success(request, _('Article ajouté au panier'))
        return redirect('orders:cart')


class UpdateCartView(LoginRequiredMixin, View):
    """Mettre à jour le panier."""
    def post(self, request):
        # Logique de mise à jour à implémenter
        messages.success(request, _('Panier mis à jour'))
        return redirect('orders:cart')


class RemoveFromCartView(LoginRequiredMixin, View):
    """Supprimer un article du panier."""
    def post(self, request):
        # Logique de suppression à implémenter
        messages.success(request, _('Article supprimé du panier'))
        return redirect('orders:cart')


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_order_list(request):
    """API liste des commandes."""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    data = []
    
    for order in orders:
        data.append({
            'id': str(order.id),
            'restaurant': order.restaurant.name,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at,
            'estimated_delivery': order.estimated_delivery_time,
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_order_detail(request, pk):
    """API détail d'une commande."""
    try:
        order = Order.objects.get(pk=pk, customer=request.user)
        data = {
            'id': str(order.id),
            'restaurant': order.restaurant.name,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at,
            'estimated_delivery': order.estimated_delivery_time,
            'delivery_address': order.delivery_address,
        }
        return Response(data, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_order_create(request):
    """API création d'une commande."""
    # À implémenter avec la logique complète
    return Response({'message': 'Order creation not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_order_status(request, pk):
    """API mise à jour du statut d'une commande."""
    # À implémenter
    return Response({'message': 'Status update not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_cart(request):
    """API gestion du panier."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        cart_items = CartItem.objects.filter(cart=cart)
        data = {
            'total_items': sum(item.quantity for item in cart_items),
            'total_amount': sum(item.get_total_price() for item in cart_items),
            'items': []
        }
        
        for item in cart_items:
            data['items'].append({
                'id': item.id,
                'menu_item': item.menu_item.name,
                'quantity': item.quantity,
                'price': float(item.menu_item.price),
                'total': float(item.get_total_price())
            })
        
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Logique d'ajout au panier à implémenter
        return Response({'message': 'Cart add not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
