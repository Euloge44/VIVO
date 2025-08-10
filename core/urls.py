"""
URLs pour l'application core.
Pages principales et utilitaires.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Page d'accueil
    path('', views.HomeView.as_view(), name='home'),
    
    # Pages statiques
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    
    # Recherche globale
    path('search/', views.SearchView.as_view(), name='search'),
    
    # API endpoints
    path('api/cities/', views.api_cities, name='api_cities'),
    path('api/contact/', views.api_contact, name='api_contact'),
    path('api/search/', views.api_search, name='api_search'),
]