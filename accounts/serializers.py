"""
Serializers pour l'application accounts.
Gestion de la sérialisation des données utilisateur pour l'API REST.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, UserDevice


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle CustomUser.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'address', 'city', 'postal_code', 'country',
            'language_preference', 'timezone', 'profile_image', 'is_active',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'full_name']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur.
    """
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'date_of_birth', 'gender', 'dietary_preferences',
            'allergies', 'email_notifications', 'sms_notifications',
            'push_notifications', 'default_delivery_address', 'delivery_instructions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un utilisateur.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'address', 'city', 'language_preference',
            'password', 'password_confirm'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        """Valider l'unicité de l'email."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('Un compte avec cet email existe déjà.'))
        return value
    
    def validate(self, attrs):
        """Valider que les mots de passe correspondent."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(_('Les mots de passe ne correspondent pas.'))
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Créer le profil utilisateur
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion utilisateur.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Valider les identifiants de connexion."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
                
                if user:
                    if not user.is_active:
                        raise serializers.ValidationError(_('Ce compte est désactivé.'))
                    attrs['user'] = user
                else:
                    raise serializers.ValidationError(_('Email ou mot de passe incorrect.'))
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(_('Email ou mot de passe incorrect.'))
        else:
            raise serializers.ValidationError(_('Email et mot de passe requis.'))
        
        return attrs


class UserDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer pour les appareils utilisateur.
    """
    class Meta:
        model = UserDevice
        fields = [
            'id', 'device_type', 'device_name', 'device_id', 'fcm_token',
            'push_notifications_enabled', 'is_active', 'last_used',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used']


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """Valider l'ancien mot de passe."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Ancien mot de passe incorrect.'))
        return value
    
    def validate(self, attrs):
        """Valider que les nouveaux mots de passe correspondent."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(_('Les nouveaux mots de passe ne correspondent pas.'))
        return attrs
    
    def save(self):
        """Sauvegarder le nouveau mot de passe."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques utilisateur.
    """
    orders_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    favorite_restaurants = serializers.IntegerField()
    loyalty_points = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    last_order_date = serializers.DateTimeField()


class RestaurantOwnerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les propriétaires de restaurant.
    """
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_status = serializers.CharField(source='restaurant.status', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'restaurant_name', 'restaurant_status', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class DeliveryPersonSerializer(serializers.ModelSerializer):
    """
    Serializer pour les livreurs.
    """
    delivery_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'delivery_stats', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'delivery_stats']
    
    def get_delivery_stats(self, obj):
        """Obtenir les statistiques de livraison."""
        # À implémenter avec les modèles de livraison
        return {
            'total_deliveries': 0,
            'rating': 0.0,
            'earnings_today': 0.0,
            'is_available': False
        }