"""
Formulaires pour l'application core.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Formulaire de contact.
    """
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'subject',
            'message',
            Submit('submit', _('Envoyer le message'), css_class='btn btn-primary')
        )


class SearchForm(forms.Form):
    """
    Formulaire de recherche globale.
    """
    query = forms.CharField(
        label=_('Rechercher'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Rechercher un restaurant, un plat...'),
            'autocomplete': 'off'
        })
    )
    category = forms.CharField(
        label=_('Catégorie'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Toutes les catégories')
        })
    )
    location = forms.CharField(
        label=_('Localisation'),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre adresse ou ville')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-3 mb-0'),
                Column('location', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', _('Rechercher'), css_class='btn btn-primary')
        )


class NewsletterForm(forms.Form):
    """
    Formulaire d'inscription à la newsletter.
    """
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre email')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'email',
            Submit('submit', _('S\'abonner'), css_class='btn btn-success')
        )