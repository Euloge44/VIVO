"""
Vues pour l'application reviews.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Review


class ReviewListView(ListView):
    """Liste des avis."""
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 20


class ReviewDetailView(DetailView):
    """Détail d'un avis."""
    model = Review
    template_name = 'reviews/detail.html'
    context_object_name = 'review'


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Création d'un avis."""
    model = Review
    template_name = 'reviews/create.html'
    fields = ['restaurant', 'rating', 'title', 'comment']
    
    def form_valid(self, form):
        form.instance.customer = self.request.user
        return super().form_valid(form)


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    """Modification d'un avis."""
    model = Review
    template_name = 'reviews/edit.html'
    fields = ['rating', 'title', 'comment']
    
    def get_queryset(self):
        return Review.objects.filter(customer=self.request.user)


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'un avis."""
    model = Review
    template_name = 'reviews/delete.html'
    
    def get_queryset(self):
        return Review.objects.filter(customer=self.request.user)


class MarkReviewHelpfulView(LoginRequiredMixin, View):
    """Marquer un avis comme utile."""
    def post(self, request, pk):
        # Logique à implémenter
        messages.success(request, _('Avis marqué comme utile'))
        return redirect('reviews:detail', pk=pk)


class ReportReviewView(LoginRequiredMixin, View):
    """Signaler un avis."""
    def post(self, request, pk):
        # Logique à implémenter
        messages.success(request, _('Avis signalé'))
        return redirect('reviews:detail', pk=pk)


# API Views
@api_view(['GET'])
def api_review_list(request):
    """API liste des avis."""
    reviews = Review.objects.all().order_by('-created_at')[:20]
    data = []
    
    for review in reviews:
        data.append({
            'id': review.id,
            'restaurant': review.restaurant.name,
            'customer': review.customer.get_full_name(),
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at,
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_review_create(request):
    """API création d'un avis."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
def api_review_detail(request, pk):
    """API détail d'un avis."""
    try:
        review = Review.objects.get(pk=pk)
        data = {
            'id': review.id,
            'restaurant': review.restaurant.name,
            'customer': review.customer.get_full_name(),
            'rating': review.rating,
            'title': review.title,
            'comment': review.comment,
            'created_at': review.created_at,
        }
        return Response(data, status=status.HTTP_200_OK)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_helpful(request, pk):
    """API marquer comme utile."""
    # À implémenter
    return Response({'message': 'Not implemented yet'}, status=status.HTTP_501_NOT_IMPLEMENTED)
