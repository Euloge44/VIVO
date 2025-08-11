"""
ViewSets pour l'API REST de l'application accounts.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, UserDevice
from .serializers import (
    CustomUserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    UserLoginSerializer, UserDeviceSerializer, PasswordChangeSerializer,
    UserStatsSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon les permissions."""
        user = self.request.user
        if user.is_superuser:
            return CustomUser.objects.all()
        elif user.user_type == 'admin':
            return CustomUser.objects.exclude(user_type='admin')
        else:
            return CustomUser.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Inscription d'un nouvel utilisateur."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': CustomUserSerializer(user).data,
                'message': _('Inscription réussie.')
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Connexion utilisateur."""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': CustomUserSerializer(user).data,
                'message': _('Connexion réussie.')
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Déconnexion utilisateur."""
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        return Response({
            'message': _('Déconnexion réussie.')
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Profil de l'utilisateur connecté."""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        return Response({
            'user': CustomUserSerializer(request.user).data,
            'profile': UserProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Mise à jour du profil."""
        user_serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        
        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            
            return Response({
                'user': user_serializer.data,
                'profile': profile_serializer.data,
                'message': _('Profil mis à jour avec succès.')
            }, status=status.HTTP_200_OK)
        
        errors = {}
        errors.update(user_serializer.errors)
        errors.update(profile_serializer.errors)
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Changement de mot de passe."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': _('Mot de passe changé avec succès.')
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques utilisateur."""
        user = request.user
        
        # Calculer les statistiques selon le type d'utilisateur
        if user.user_type == 'client':
            stats = {
                'orders_count': 0,  # À implémenter avec Order.objects.filter(customer=user).count()
                'total_spent': 0,   # À implémenter
                'favorite_restaurants': 0,  # À implémenter
                'loyalty_points': 0,  # À implémenter
                'reviews_count': 0,  # À implémenter
                'last_order_date': None,  # À implémenter
            }
        elif user.user_type == 'restaurant':
            stats = {
                'orders_count': 0,  # À implémenter
                'total_spent': 0,
                'favorite_restaurants': 0,
                'loyalty_points': 0,
                'reviews_count': 0,
                'last_order_date': None,
            }
        elif user.user_type == 'delivery':
            stats = {
                'orders_count': 0,
                'total_spent': 0,
                'favorite_restaurants': 0,
                'loyalty_points': 0,
                'reviews_count': 0,
                'last_order_date': None,
            }
        else:
            stats = {}
        
        return Response(stats, status=status.HTTP_200_OK)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les profils utilisateur.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur."""
        return UserProfile.objects.filter(user=self.request.user)


class UserDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les appareils utilisateur.
    """
    queryset = UserDevice.objects.all()
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon l'utilisateur."""
        return UserDevice.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Assigner l'utilisateur lors de la création."""
        serializer.save(user=self.request.user)