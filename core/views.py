"""
Vues principales pour l'application core.
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import SiteSettings, FAQ, ContactMessage, City
from .forms import ContactForm


class HomeView(TemplateView):
    """
    Page d'accueil principale.
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Données pour la page d'accueil
        context.update({
            'featured_restaurants': [],  # À implémenter avec les modèles Restaurant
            'popular_categories': [],  # À implémenter
            'recent_reviews': [],  # À implémenter
            'site_stats': {
                'restaurants_count': 0,
                'orders_count': 0,
                'users_count': 0,
            }
        })
        
        return context


class AboutView(TemplateView):
    """
    Page à propos.
    """
    template_name = 'core/about.html'


class ContactView(View):
    """
    Page de contact avec formulaire.
    """
    template_name = 'core/contact.html'
    form_class = ContactForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            # Sauvegarder le message
            contact_message = ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                user=request.user if request.user.is_authenticated else None
            )
            
            messages.success(request, _('Votre message a été envoyé avec succès. Nous vous répondrons bientôt.'))
            return redirect('core:contact')
        
        return render(request, self.template_name, {'form': form})


class FAQView(ListView):
    """
    Page FAQ.
    """
    model = FAQ
    template_name = 'core/faq.html'
    context_object_name = 'faqs'
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).order_by('order', 'question')


class TermsView(TemplateView):
    """
    Conditions d'utilisation.
    """
    template_name = 'core/terms.html'


class PrivacyView(TemplateView):
    """
    Politique de confidentialité.
    """
    template_name = 'core/privacy.html'


class SearchView(View):
    """
    Vue de recherche globale.
    """
    template_name = 'core/search.html'
    
    def get(self, request):
        query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        location = request.GET.get('location', '')
        
        context = {
            'query': query,
            'category': category,
            'location': location,
            'results': {
                'restaurants': [],  # À implémenter
                'menu_items': [],  # À implémenter
                'total_count': 0,
            }
        }
        
        if query:
            # Ici on implémentera la recherche dans les restaurants et menus
            pass
        
        return render(request, self.template_name, context)


# API Views
@api_view(['GET'])
def api_cities(request):
    """
    API pour récupérer la liste des villes.
    """
    cities = City.objects.filter(is_active=True).values('id', 'name', 'country__name')
    return Response(list(cities), status=status.HTTP_200_OK)


@api_view(['POST'])
def api_contact(request):
    """
    API pour envoyer un message de contact.
    """
    form = ContactForm(request.data)
    
    if form.is_valid():
        ContactMessage.objects.create(
            name=form.cleaned_data['name'],
            email=form.cleaned_data['email'],
            subject=form.cleaned_data['subject'],
            message=form.cleaned_data['message'],
            user=request.user if request.user.is_authenticated else None
        )
        
        return Response({
            'message': _('Message envoyé avec succès.')
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'errors': form.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def api_search(request):
    """
    API de recherche globale.
    """
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    limit = int(request.GET.get('limit', 20))
    
    results = {
        'restaurants': [],
        'menu_items': [],
        'total_count': 0,
    }
    
    if query:
        # Ici on implémentera la recherche
        # Pour l'instant, on retourne des résultats vides
        pass
    
    return Response(results, status=status.HTTP_200_OK)
