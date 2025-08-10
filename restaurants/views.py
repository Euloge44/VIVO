"""
Vues pour l'application restaurants.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, MenuItem, Category


class RestaurantListView(ListView):
    """Liste des restaurants."""
    model = Restaurant
    template_name = 'restaurants/list.html'
    context_object_name = 'restaurants'
    paginate_by = 12
    
    def get_queryset(self):
        return Restaurant.objects.filter(is_active=True).select_related('owner')


class RestaurantDetailView(DetailView):
    """Détail d'un restaurant."""
    model = Restaurant
    template_name = 'restaurants/detail.html'
    context_object_name = 'restaurant'
    
    def get_queryset(self):
        return Restaurant.objects.filter(is_active=True)


class RestaurantMenuView(DetailView):
    """Menu d'un restaurant."""
    model = Restaurant
    template_name = 'restaurants/menu.html'
    context_object_name = 'restaurant'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_items'] = MenuItem.objects.filter(
            restaurant=self.object, 
            is_available=True
        ).select_related('category')
        return context


class RestaurantDashboardView(LoginRequiredMixin, DetailView):
    """Tableau de bord restaurant."""
    model = Restaurant
    template_name = 'restaurants/dashboard.html'
    context_object_name = 'restaurant'
    
    def get_object(self):
        return get_object_or_404(Restaurant, owner=self.request.user)


class MenuManagementView(LoginRequiredMixin, ListView):
    """Gestion du menu."""
    model = MenuItem
    template_name = 'restaurants/menu_management.html'
    context_object_name = 'menu_items'
    
    def get_queryset(self):
        restaurant = get_object_or_404(Restaurant, owner=self.request.user)
        return MenuItem.objects.filter(restaurant=restaurant)


class OrderManagementView(LoginRequiredMixin, ListView):
    """Gestion des commandes."""
    template_name = 'restaurants/order_management.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        # Sera implémenté avec les modèles Order
        return []


class RestaurantStatsView(LoginRequiredMixin, DetailView):
    """Statistiques du restaurant."""
    model = Restaurant
    template_name = 'restaurants/stats.html'
    context_object_name = 'restaurant'
    
    def get_object(self):
        return get_object_or_404(Restaurant, owner=self.request.user)


# API Views
@api_view(['GET'])
def api_restaurant_list(request):
    """API liste des restaurants."""
    restaurants = Restaurant.objects.filter(is_active=True)
    data = []
    
    for restaurant in restaurants:
        data.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'rating': restaurant.average_rating,
            'delivery_time': restaurant.estimated_delivery_time,
            'is_open': restaurant.is_open_now(),
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_restaurant_detail(request, pk):
    """API détail d'un restaurant."""
    try:
        restaurant = Restaurant.objects.get(pk=pk, is_active=True)
        data = {
            'id': restaurant.id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'phone': restaurant.phone,
            'rating': restaurant.average_rating,
            'delivery_time': restaurant.estimated_delivery_time,
            'is_open': restaurant.is_open_now(),
            'latitude': float(restaurant.latitude) if restaurant.latitude else None,
            'longitude': float(restaurant.longitude) if restaurant.longitude else None,
        }
        return Response(data, status=status.HTTP_200_OK)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_restaurant_menu(request, pk):
    """API menu d'un restaurant."""
    try:
        restaurant = Restaurant.objects.get(pk=pk, is_active=True)
        menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
        
        data = []
        for item in menu_items:
            data.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': float(item.price),
                'category': item.category.name if item.category else None,
                'preparation_time': item.preparation_time,
                'is_vegetarian': item.is_vegetarian,
                'is_vegan': item.is_vegan,
                'allergens': item.allergens,
            })
        
        return Response(data, status=status.HTTP_200_OK)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_restaurant_search(request):
    """API recherche de restaurants."""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    restaurants = Restaurant.objects.filter(is_active=True)
    
    if query:
        restaurants = restaurants.filter(name__icontains=query)
    
    if category:
        restaurants = restaurants.filter(categories__name__icontains=category)
    
    data = []
    for restaurant in restaurants[:20]:  # Limiter à 20 résultats
        data.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'description': restaurant.description,
            'address': restaurant.address,
            'rating': restaurant.average_rating,
            'is_open': restaurant.is_open_now(),
        })
    
    return Response(data, status=status.HTTP_200_OK)
