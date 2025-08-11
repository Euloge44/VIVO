"""
Vues d'authentification pour GourmetGuide.
Support des différents types d'utilisateurs avec redirection appropriée.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DetailView
from django.views import View
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import CustomUser, UserProfile
from .forms import (
    CustomUserCreationForm, ClientRegistrationForm, 
    RestaurantRegistrationForm, DeliveryPersonRegistrationForm,
    ProfileUpdateForm, UserPreferencesForm, CustomLoginForm
)


class CustomLoginView(View):
    """
    Vue de connexion personnalisée avec redirection basée sur le type d'utilisateur.
    """
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    
    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_user(request.user)
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            try:
                user = CustomUser.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        
                        # Configurer la session
                        if not remember_me:
                            request.session.set_expiry(0)
                        
                        messages.success(request, _('Connexion réussie ! Bienvenue {}').format(user.get_full_name()))
                        
                        # Redirection basée sur le type d'utilisateur
                        next_url = request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        
                        return self.redirect_user(user)
                    else:
                        messages.error(request, _('Votre compte est désactivé.'))
                else:
                    messages.error(request, _('Email ou mot de passe incorrect.'))
            except CustomUser.DoesNotExist:
                messages.error(request, _('Email ou mot de passe incorrect.'))
        
        return render(request, self.template_name, {'form': form})
    
    def redirect_user(self, user):
        """Redirige l'utilisateur selon son type."""
        if user.user_type == 'admin':
            return redirect('admin:index')
        elif user.user_type == 'restaurant':
            return redirect('restaurants:dashboard')
        elif user.user_type == 'delivery':
            return redirect('delivery:dashboard')
        else:  # client
            return redirect('core:home')


class RegisterView(CreateView):
    """
    Vue d'inscription générale.
    """
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:login')
    
    def get_form_class(self):
        """Retourne le formulaire approprié selon le type d'utilisateur."""
        user_type = self.request.GET.get('type', 'client')
        
        if user_type == 'restaurant':
            return RestaurantRegistrationForm
        elif user_type == 'delivery':
            return DeliveryPersonRegistrationForm
        else:
            return ClientRegistrationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.request.GET.get('type', 'client')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        
        # Créer les objets associés selon le type d'utilisateur
        if user.user_type == 'restaurant':
            self.create_restaurant_profile(user, form)
        elif user.user_type == 'delivery':
            self.create_delivery_profile(user, form)
        
        messages.success(
            self.request, 
            _('Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.')
        )
        return response
    
    def create_restaurant_profile(self, user, form):
        """Crée le profil restaurant."""
        from restaurants.models import Restaurant
        
        Restaurant.objects.create(
            owner=user,
            name=form.cleaned_data.get('restaurant_name'),
            description=form.cleaned_data.get('restaurant_description'),
            address=form.cleaned_data.get('restaurant_address'),
            phone=form.cleaned_data.get('restaurant_phone'),
            is_active=False  # Nécessite validation admin
        )
    
    def create_delivery_profile(self, user, form):
        """Crée le profil livreur."""
        from delivery.models import DeliveryPerson
        
        DeliveryPerson.objects.create(
            user=user,
            vehicle_type=form.cleaned_data.get('vehicle_type'),
            license_number=form.cleaned_data.get('license_number'),
            vehicle_registration=form.cleaned_data.get('vehicle_registration'),
            is_verified=False  # Nécessite validation admin
        )


class ProfileView(LoginRequiredMixin, DetailView):
    """
    Vue du profil utilisateur.
    """
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vue de mise à jour du profil.
    """
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Votre profil a été mis à jour avec succès.'))
        return super().form_valid(form)


class UserPreferencesView(LoginRequiredMixin, UpdateView):
    """
    Vue de gestion des préférences utilisateur.
    """
    model = UserProfile
    form_class = UserPreferencesForm
    template_name = 'accounts/preferences.html'
    success_url = reverse_lazy('accounts:preferences')
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, _('Vos préférences ont été sauvegardées.'))
        return super().form_valid(form)


class CustomLogoutView(View):
    """
    Vue de déconnexion personnalisée.
    """
    def get(self, request):
        logout(request)
        messages.success(request, _('Vous avez été déconnecté avec succès.'))
        return redirect('core:home')


# API Views pour l'authentification mobile/AJAX
@api_view(['POST'])
def api_login(request):
    """
    API de connexion pour applications mobiles.
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': _('Email et mot de passe requis.')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email)
        user = authenticate(request, username=user.username, password=password)
        
        if user is not None:
            if user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.id,
                    'user_type': user.user_type,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'message': _('Connexion réussie.')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': _('Compte désactivé.')
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'error': _('Identifiants incorrects.')
            }, status=status.HTTP_401_UNAUTHORIZED)
    except CustomUser.DoesNotExist:
        return Response({
            'error': _('Identifiants incorrects.')
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def api_register(request):
    """
    API d'inscription pour applications mobiles.
    """
    user_type = request.data.get('user_type', 'client')
    
    # Sélectionner le bon formulaire
    if user_type == 'restaurant':
        form_class = RestaurantRegistrationForm
    elif user_type == 'delivery':
        form_class = DeliveryPersonRegistrationForm
    else:
        form_class = ClientRegistrationForm
    
    form = form_class(request.data)
    
    if form.is_valid():
        user = form.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'user_type': user.user_type,
            'email': user.email,
            'full_name': user.get_full_name(),
            'message': _('Inscription réussie.')
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'errors': form.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    API de déconnexion pour applications mobiles.
    """
    try:
        request.user.auth_token.delete()
        return Response({
            'message': _('Déconnexion réussie.')
        }, status=status.HTTP_200_OK)
    except:
        return Response({
            'message': _('Déconnexion réussie.')
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """
    API pour récupérer le profil utilisateur.
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    return Response({
        'user_id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'user_type': user.user_type,
        'address': user.address,
        'city': user.city,
        'postal_code': user.postal_code,
        'language_preference': user.language_preference,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'profile': {
            'bio': profile.bio,
            'date_of_birth': profile.date_of_birth,
            'gender': profile.gender,
            'dietary_preferences': profile.dietary_preferences,
            'allergies': profile.allergies,
            'email_notifications': profile.email_notifications,
            'sms_notifications': profile.sms_notifications,
            'push_notifications': profile.push_notifications,
        }
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_update_profile(request):
    """
    API pour mettre à jour le profil utilisateur.
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Mettre à jour les champs utilisateur
    user_fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'postal_code', 'language_preference']
    for field in user_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    
    # Mettre à jour les champs du profil
    profile_fields = ['bio', 'date_of_birth', 'gender', 'dietary_preferences', 'allergies', 
                     'email_notifications', 'sms_notifications', 'push_notifications']
    for field in profile_fields:
        if field in request.data:
            setattr(profile, field, request.data[field])
    
    try:
        user.full_clean()
        profile.full_clean()
        user.save()
        profile.save()
        
        return Response({
            'message': _('Profil mis à jour avec succès.')
        }, status=status.HTTP_200_OK)
    except ValidationError as e:
        return Response({
            'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


def register_choice_view(request):
    """
    Vue pour choisir le type d'inscription.
    """
    return render(request, 'accounts/register_choice.html')


# Vues spécifiques pour chaque type d'utilisateur
class ClientDashboardView(LoginRequiredMixin, View):
    """
    Tableau de bord pour les clients.
    """
    def get(self, request):
        if request.user.user_type != 'client':
            messages.error(request, _('Accès non autorisé.'))
            return redirect('accounts:login')
        
        context = {
            'recent_orders': [],  # À implémenter avec les modèles Order
            'favorite_restaurants': [],  # À implémenter
            'loyalty_points': 0,  # À implémenter avec le système de fidélité
        }
        return render(request, 'accounts/client_dashboard.html', context)


class RestaurantDashboardView(LoginRequiredMixin, View):
    """
    Tableau de bord pour les restaurants.
    """
    def get(self, request):
        if request.user.user_type != 'restaurant':
            messages.error(request, _('Accès non autorisé.'))
            return redirect('accounts:login')
        
        context = {
            'pending_orders': [],  # À implémenter
            'today_revenue': 0,  # À implémenter
            'menu_items_count': 0,  # À implémenter
        }
        return render(request, 'accounts/restaurant_dashboard.html', context)


class DeliveryDashboardView(LoginRequiredMixin, View):
    """
    Tableau de bord pour les livreurs.
    """
    def get(self, request):
        if request.user.user_type != 'delivery':
            messages.error(request, _('Accès non autorisé.'))
            return redirect('accounts:login')
        
        context = {
            'available_deliveries': [],  # À implémenter
            'today_deliveries': 0,  # À implémenter
            'earnings': 0,  # À implémenter
        }
        return render(request, 'accounts/delivery_dashboard.html', context)


class AdminDashboardView(LoginRequiredMixin, View):
    """
    Tableau de bord pour les administrateurs.
    """
    def get(self, request):
        if not request.user.is_staff and request.user.user_type != 'admin':
            messages.error(request, _('Accès non autorisé.'))
            return redirect('accounts:login')
        
        context = {
            'total_users': CustomUser.objects.count(),
            'total_restaurants': 0,  # À implémenter
            'total_orders': 0,  # À implémenter
            'pending_approvals': 0,  # À implémenter
        }
        return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def switch_language(request):
    """
    Change la langue de l'utilisateur.
    """
    language = request.POST.get('language')
    if language:
        request.user.language_preference = language
        request.user.save()
        
        # Activer la langue pour cette session
        from django.utils import translation
        translation.activate(language)
        request.session[translation.LANGUAGE_SESSION_KEY] = language
        
        messages.success(request, _('Langue changée avec succès.'))
    
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
def delete_account(request):
    """
    Supprime le compte utilisateur (avec confirmation).
    """
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if request.user.check_password(password):
            # Marquer comme inactif plutôt que supprimer complètement
            request.user.is_active = False
            request.user.save()
            
            logout(request)
            messages.success(request, _('Votre compte a été désactivé avec succès.'))
            return redirect('core:home')
        else:
            messages.error(request, _('Mot de passe incorrect.'))
    
    return render(request, 'accounts/delete_account.html')


# Vues API pour la gestion des utilisateurs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_stats(request):
    """
    Statistiques utilisateur pour le tableau de bord.
    """
    user = request.user
    stats = {}
    
    if user.user_type == 'client':
        stats = {
            'orders_count': 0,  # À implémenter
            'favorite_restaurants': 0,  # À implémenter
            'loyalty_points': 0,  # À implémenter
            'reviews_count': 0,  # À implémenter
        }
    elif user.user_type == 'restaurant':
        stats = {
            'orders_count': 0,  # À implémenter
            'menu_items': 0,  # À implémenter
            'reviews_avg': 0,  # À implémenter
            'revenue_today': 0,  # À implémenter
        }
    elif user.user_type == 'delivery':
        stats = {
            'deliveries_count': 0,  # À implémenter
            'earnings_today': 0,  # À implémenter
            'rating_avg': 0,  # À implémenter
            'distance_today': 0,  # À implémenter
        }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_avatar(request):
    """
    API pour télécharger une photo de profil.
    """
    # Pour l'instant, on simule avec une URL
    avatar_url = request.data.get('avatar_url', '')
    
    if avatar_url:
        request.user.profile_image = avatar_url
        request.user.save()
        
        return Response({
            'message': _('Photo de profil mise à jour.'),
            'avatar_url': avatar_url
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': _('URL de l\'image requise.')
    }, status=status.HTTP_400_BAD_REQUEST)
