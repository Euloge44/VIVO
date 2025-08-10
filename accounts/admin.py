"""
Configuration de l'administration Django pour les comptes utilisateurs.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import CustomUser, UserProfile, UserDevice


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Administration personnalisée pour CustomUser.
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined', 'language_preference')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_image')
        }),
        (_('Type et rôle'), {
            'fields': ('user_type', 'is_staff', 'is_active', 'is_superuser')
        }),
        (_('Adresse'), {
            'fields': ('address', 'city', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        (_('Préférences'), {
            'fields': ('language_preference', 'timezone'),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user_type__in=['client', 'delivery'])
    
    def has_change_permission(self, request, obj=None):
        if obj and obj.user_type == 'admin' and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.user_type == 'admin' and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Administration pour les profils utilisateurs.
    """
    list_display = ('user', 'get_user_type', 'email_notifications', 'created_at')
    list_filter = ('email_notifications', 'sms_notifications', 'push_notifications', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Utilisateur'), {
            'fields': ('user',)
        }),
        (_('Informations personnelles'), {
            'fields': ('bio',)
        }),
        (_('Préférences alimentaires'), {
            'fields': ('dietary_preferences', 'allergies'),
            'classes': ('collapse',)
        }),
        (_('Notifications'), {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        (_('Livraison'), {
            'fields': ('default_delivery_address', 'delivery_instructions'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_type(self, obj):
        return obj.user.get_user_type_display()
    get_user_type.short_description = _('Type d\'utilisateur')
    get_user_type.admin_order_field = 'user__user_type'


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    """
    Administration pour les appareils utilisateurs.
    """
    list_display = ('user', 'device_type', 'device_name', 'is_active', 'last_used', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'device_name', 'device_id', 'fcm_token')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Utilisateur'), {
            'fields': ('user',)
        }),
        (_('Informations de l\'appareil'), {
            'fields': ('device_type', 'device_name', 'device_id', 'is_active')
        }),
        (_('Notifications'), {
            'fields': ('fcm_token', 'push_notifications_enabled'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('last_used', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Les utilisateurs ne peuvent voir que leurs propres appareils
        if hasattr(request.user, 'userdevice_set'):
            return qs.filter(user=request.user)
        return qs.none()


# Configuration de l'admin principal
admin.site.site_header = _('Administration GourmetGuide')
admin.site.site_title = _('GourmetGuide Admin')
admin.site.index_title = _('Tableau de bord administrateur')
