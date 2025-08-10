"""
Formulaires d'authentification pour GourmetGuide.
Support des différents types d'utilisateurs.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, HTML
from crispy_forms.bootstrap import PrependedText, AppendedText
from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire de création d'utilisateur personnalisé.
    """
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label=_('Prénom'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_('Nom'),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label=_('Téléphone'),
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+228 XX XX XX XX'})
    )
    user_type = forms.ChoiceField(
        label=_('Type de compte'),
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Informations personnelles'),
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'email',
                'username',
                PrependedText('phone', '+228', placeholder='XX XX XX XX'),
                'user_type',
            ),
            Fieldset(
                _('Sécurité'),
                'password1',
                'password2',
            ),
            Submit('submit', _('Créer le compte'), css_class='btn btn-primary btn-lg')
        )
        
        # Rendre l'email obligatoire et unique
        self.fields['email'].required = True
        self.fields['username'].help_text = _('Optionnel. Sera généré automatiquement si vide.')
        self.fields['username'].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_('Un compte avec cet email existe déjà.'))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            # Générer un username basé sur l'email
            email = self.cleaned_data.get('email', '')
            if email:
                username = email.split('@')[0]
                counter = 1
                original_username = username
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Créer le profil utilisateur
            UserProfile.objects.create(user=user)
        return user


class ClientRegistrationForm(CustomUserCreationForm):
    """
    Formulaire spécifique pour l'inscription des clients.
    """
    address = forms.CharField(
        label=_('Adresse'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    city = forms.CharField(
        label=_('Ville'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + ('address', 'city')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'client'
        self.fields['user_type'].widget = forms.HiddenInput()


class RestaurantRegistrationForm(CustomUserCreationForm):
    """
    Formulaire spécifique pour l'inscription des restaurants.
    """
    restaurant_name = forms.CharField(
        label=_('Nom du restaurant'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    restaurant_description = forms.CharField(
        label=_('Description du restaurant'),
        required=True,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
    )
    restaurant_address = forms.CharField(
        label=_('Adresse du restaurant'),
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    restaurant_phone = forms.CharField(
        label=_('Téléphone du restaurant'),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + ('restaurant_name', 'restaurant_description', 'restaurant_address', 'restaurant_phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'restaurant'
        self.fields['user_type'].widget = forms.HiddenInput()


class DeliveryPersonRegistrationForm(CustomUserCreationForm):
    """
    Formulaire spécifique pour l'inscription des livreurs.
    """
    vehicle_type = forms.ChoiceField(
        label=_('Type de véhicule'),
        choices=[
            ('bike', _('Vélo')),
            ('motorbike', _('Moto')),
            ('car', _('Voiture')),
            ('scooter', _('Scooter')),
            ('walking', _('À pied')),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    license_number = forms.CharField(
        label=_('Numéro de permis'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    vehicle_registration = forms.CharField(
        label=_('Immatriculation'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + ('vehicle_type', 'license_number', 'vehicle_registration')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].initial = 'delivery'
        self.fields['user_type'].widget = forms.HiddenInput()


class ProfileUpdateForm(forms.ModelForm):
    """
    Formulaire de mise à jour du profil utilisateur.
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'postal_code', 'language_preference']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'language_preference': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Informations personnelles'),
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                PrependedText('phone', '+228'),
                'language_preference',
            ),
            Fieldset(
                _('Adresse'),
                'address',
                Row(
                    Column('city', css_class='form-group col-md-8 mb-0'),
                    Column('postal_code', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Submit('submit', _('Mettre à jour'), css_class='btn btn-primary')
        )


class UserPreferencesForm(forms.ModelForm):
    """
    Formulaire pour les préférences utilisateur.
    """
    class Meta:
        model = UserProfile
        fields = [
            'dietary_preferences', 'allergies', 'email_notifications', 
            'sms_notifications', 'push_notifications', 'default_delivery_address',
            'delivery_instructions'
        ]
        widgets = {
            'dietary_preferences': forms.CheckboxSelectMultiple(),
            'allergies': forms.CheckboxSelectMultiple(),
            'default_delivery_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'delivery_instructions': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Préférences alimentaires'),
                'dietary_preferences',
                'allergies',
            ),
            Fieldset(
                _('Notifications'),
                'email_notifications',
                'sms_notifications', 
                'push_notifications',
            ),
            Fieldset(
                _('Livraison'),
                'default_delivery_address',
                'delivery_instructions',
            ),
            Submit('submit', _('Sauvegarder'), css_class='btn btn-primary')
        )


class CustomLoginForm(forms.Form):
    """
    Formulaire de connexion personnalisé.
    """
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre email'),
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre mot de passe')
        })
    )
    remember_me = forms.BooleanField(
        label=_('Se souvenir de moi'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'email',
            'password',
            'remember_me',
            Submit('submit', _('Se connecter'), css_class='btn btn-primary btn-lg w-100')
        )