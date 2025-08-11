"""
Formulaires pour l'application payments.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, HTML, Div
from crispy_forms.bootstrap import PrependedText, AppendedText

from .models import Payment, Wallet, WalletTransaction
from .utils import validate_payment_amount, get_available_payment_methods


class PaymentForm(forms.ModelForm):
    """Formulaire de paiement principal."""
    
    payment_method = forms.ChoiceField(
        label=_("Méthode de paiement"),
        choices=[],
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'})
    )
    
    # Champs pour paiement mobile
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+228 XX XX XX XX',
            'class': 'form-control'
        })
    )
    
    # Champs pour Stripe
    save_card = forms.BooleanField(
        label=_("Enregistrer cette carte pour les prochains paiements"),
        required=False
    )
    
    class Meta:
        model = Payment
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # Définir les choix de méthode de paiement
        if self.user:
            methods = get_available_payment_methods(self.user, self.instance.amount if self.instance else None)
            self.fields['payment_method'].choices = [
                (method['id'], method['name']) for method in methods
            ]
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _("Détails du paiement"),
                PrependedText('amount', 'FCFA', readonly=True),
                'payment_method',
            ),
            Div(
                Fieldset(
                    _("Informations de paiement mobile"),
                    'phone_number',
                    css_class='mobile-payment-fields',
                    style='display: none;'
                ),
                css_class='payment-method-fields'
            ),
            Div(
                Fieldset(
                    _("Options de carte"),
                    'save_card',
                    css_class='stripe-payment-fields',
                    style='display: none;'
                ),
                css_class='payment-method-fields'
            ),
            Submit('submit', _('Procéder au paiement'), css_class='btn btn-primary btn-lg w-100')
        )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError(_("Le montant doit être positif"))
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        amount = cleaned_data.get('amount')
        phone_number = cleaned_data.get('phone_number')
        
        if payment_method and amount:
            # Valider le montant selon la méthode
            is_valid, error_msg = validate_payment_amount(amount, payment_method)
            if not is_valid:
                raise ValidationError(error_msg)
            
            # Valider le téléphone pour les paiements mobiles
            if payment_method in ['tmoney', 'flooz']:
                if not phone_number:
                    if self.user and self.user.phone:
                        cleaned_data['phone_number'] = self.user.phone
                    else:
                        raise ValidationError(_("Numéro de téléphone requis pour le paiement mobile"))
                
                # Valider le format du téléphone
                phone = cleaned_data.get('phone_number', '')
                if not self._validate_togo_phone(phone):
                    raise ValidationError(_("Format de téléphone invalide. Utilisez: +228 XX XX XX XX"))
        
        return cleaned_data
    
    def _validate_togo_phone(self, phone):
        """Valide un numéro de téléphone togolais."""
        import re
        pattern = r'^\+228\s?[0-9]{8}$'
        return bool(re.match(pattern, phone.replace(' ', '')))


class WalletTopUpForm(forms.Form):
    """Formulaire de rechargement de portefeuille."""
    
    AMOUNT_CHOICES = [
        (1000, '1,000 FCFA'),
        (2500, '2,500 FCFA'),
        (5000, '5,000 FCFA'),
        (10000, '10,000 FCFA'),
        (25000, '25,000 FCFA'),
        (50000, '50,000 FCFA'),
        (0, _('Montant personnalisé'))
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', _('Carte bancaire (Stripe)')),
        ('tmoney', _('Tmoney')),
        ('flooz', _('Flooz')),
    ]
    
    preset_amount = forms.ChoiceField(
        label=_("Montant prédéfini"),
        choices=AMOUNT_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'amount-preset'})
    )
    
    custom_amount = forms.DecimalField(
        label=_("Montant personnalisé"),
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'placeholder': _('Entrez le montant en FCFA'),
            'class': 'form-control',
            'style': 'display: none;'
        })
    )
    
    payment_method = forms.ChoiceField(
        label=_("Méthode de paiement"),
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'})
    )
    
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+228 XX XX XX XX',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Préremplir le téléphone si disponible
        if self.user and self.user.phone:
            self.fields['phone_number'].initial = self.user.phone
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _("Montant à recharger"),
                'preset_amount',
                'custom_amount',
            ),
            Fieldset(
                _("Méthode de paiement"),
                'payment_method',
                Div(
                    'phone_number',
                    css_class='mobile-payment-fields',
                    style='display: none;'
                )
            ),
            HTML('<div id="payment-fees-display" class="alert alert-info" style="display: none;"></div>'),
            Submit('submit', _('Recharger le portefeuille'), css_class='btn btn-success btn-lg w-100')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        preset_amount = cleaned_data.get('preset_amount')
        custom_amount = cleaned_data.get('custom_amount')
        payment_method = cleaned_data.get('payment_method')
        phone_number = cleaned_data.get('phone_number')
        
        # Déterminer le montant final
        if preset_amount and int(preset_amount) > 0:
            amount = Decimal(preset_amount)
        elif custom_amount:
            amount = custom_amount
        else:
            raise ValidationError(_("Veuillez sélectionner ou saisir un montant"))
        
        cleaned_data['amount'] = amount
        
        # Valider le montant selon la méthode
        if payment_method:
            is_valid, error_msg = validate_payment_amount(amount, payment_method)
            if not is_valid:
                raise ValidationError(error_msg)
            
            # Valider le téléphone pour les paiements mobiles
            if payment_method in ['tmoney', 'flooz']:
                if not phone_number:
                    if self.user and self.user.phone:
                        cleaned_data['phone_number'] = self.user.phone
                    else:
                        raise ValidationError(_("Numéro de téléphone requis"))
                
                # Valider le format
                phone = cleaned_data.get('phone_number', '')
                if not self._validate_togo_phone(phone):
                    raise ValidationError(_("Format de téléphone invalide"))
        
        return cleaned_data
    
    def _validate_togo_phone(self, phone):
        """Valide un numéro de téléphone togolais."""
        import re
        pattern = r'^\+228\s?[0-9]{8}$'
        return bool(re.match(pattern, phone.replace(' ', '')))


class MobilePaymentForm(forms.Form):
    """Formulaire spécifique pour les paiements mobiles."""
    
    PROVIDER_CHOICES = [
        ('tmoney', 'Tmoney (Togocom)'),
        ('flooz', 'Flooz (Moov)')
    ]
    
    provider = forms.ChoiceField(
        label=_("Fournisseur"),
        choices=PROVIDER_CHOICES,
        widget=forms.RadioSelect
    )
    
    phone_number = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+228 XX XX XX XX',
            'class': 'form-control'
        })
    )
    
    amount = forms.DecimalField(
        label=_("Montant"),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Préremplir le téléphone
        if self.user and self.user.phone:
            self.fields['phone_number'].initial = self.user.phone
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'provider',
            'phone_number',
            PrependedText('amount', 'FCFA'),
            HTML('''
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    {% trans "Vous recevrez un SMS avec les instructions de paiement." %}
                </div>
            '''),
            Submit('submit', _('Initier le paiement'), css_class='btn btn-primary btn-lg w-100')
        )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        
        # Valider le format togolais
        import re
        pattern = r'^\+228\s?[0-9]{8}$'
        if not re.match(pattern, phone.replace(' ', '')):
            raise ValidationError(_("Format invalide. Utilisez: +228 XX XX XX XX"))
        
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get('provider')
        amount = cleaned_data.get('amount')
        
        if provider and amount:
            # Valider selon le fournisseur
            is_valid, error_msg = validate_payment_amount(amount, provider)
            if not is_valid:
                raise ValidationError(error_msg)
        
        return cleaned_data


class WalletTransferForm(forms.Form):
    """Formulaire de transfert entre portefeuilles."""
    
    recipient_email = forms.EmailField(
        label=_("Email du destinataire"),
        widget=forms.EmailInput(attrs={
            'placeholder': _('email@exemple.com'),
            'class': 'form-control'
        })
    )
    
    amount = forms.DecimalField(
        label=_("Montant à transférer"),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'placeholder': _('Montant en FCFA'),
            'class': 'form-control'
        })
    )
    
    description = forms.CharField(
        label=_("Description (optionnelle)"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Motif du transfert...'),
            'class': 'form-control'
        })
    )
    
    confirm_transfer = forms.BooleanField(
        label=_("Je confirme vouloir effectuer ce transfert"),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _("Détails du transfert"),
                'recipient_email',
                PrependedText('amount', 'FCFA'),
                'description',
            ),
            HTML('''
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    {% trans "Les transferts sont immédiats et irréversibles." %}
                </div>
            '''),
            'confirm_transfer',
            Submit('submit', _('Effectuer le transfert'), css_class='btn btn-warning btn-lg w-100')
        )
    
    def clean_recipient_email(self):
        email = self.cleaned_data['recipient_email']
        
        # Vérifier que le destinataire existe
        from accounts.models import CustomUser
        try:
            recipient = CustomUser.objects.get(email=email)
            if self.user and recipient.id == self.user.id:
                raise ValidationError(_("Vous ne pouvez pas vous transférer à vous-même"))
        except CustomUser.DoesNotExist:
            raise ValidationError(_("Aucun utilisateur trouvé avec cet email"))
        
        return email
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        
        # Vérifier le solde suffisant
        if self.user:
            from .utils import WalletManager
            current_balance = WalletManager.get_balance(self.user.id)
            if amount > current_balance:
                raise ValidationError(
                    _("Solde insuffisant. Solde actuel: %(balance)s FCFA") % {
                        'balance': current_balance
                    }
                )
        
        return amount


class PaymentFilterForm(forms.Form):
    """Formulaire de filtrage des paiements."""
    
    STATUS_CHOICES = [
        ('', _('Tous les statuts')),
        ('pending', _('En attente')),
        ('completed', _('Complété')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
    ]
    
    METHOD_CHOICES = [
        ('', _('Toutes les méthodes')),
        ('stripe', _('Carte bancaire')),
        ('tmoney', _('Tmoney')),
        ('flooz', _('Flooz')),
        ('wallet', _('Portefeuille')),
        ('cash', _('Espèces')),
    ]
    
    status = forms.ChoiceField(
        label=_("Statut"),
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_method = forms.ChoiceField(
        label=_("Méthode"),
        choices=METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        label=_("Du"),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        label=_("Au"),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('status', css_class='col-md-3'),
                Column('payment_method', css_class='col-md-3'),
                Column('date_from', css_class='col-md-3'),
                Column('date_to', css_class='col-md-3'),
            ),
            Submit('filter', _('Filtrer'), css_class='btn btn-outline-primary')
        )


class RefundRequestForm(forms.Form):
    """Formulaire de demande de remboursement."""
    
    REASON_CHOICES = [
        ('order_cancelled', _('Commande annulée')),
        ('wrong_order', _('Erreur de commande')),
        ('quality_issue', _('Problème de qualité')),
        ('delivery_issue', _('Problème de livraison')),
        ('other', _('Autre'))
    ]
    
    reason = forms.ChoiceField(
        label=_("Motif du remboursement"),
        choices=REASON_CHOICES,
        widget=forms.RadioSelect
    )
    
    description = forms.CharField(
        label=_("Description détaillée"),
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': _('Décrivez le problème en détail...'),
            'class': 'form-control'
        })
    )
    
    amount = forms.DecimalField(
        label=_("Montant à rembourser"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment', None)
        super().__init__(*args, **kwargs)
        
        if self.payment:
            self.fields['amount'].initial = self.payment.amount
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'reason',
            'description',
            PrependedText('amount', 'FCFA'),
            HTML('''
                <div class="alert alert-warning">
                    <i class="fas fa-clock me-2"></i>
                    {% trans "Les demandes de remboursement sont traitées sous 3-5 jours ouvrables." %}
                </div>
            '''),
            Submit('submit', _('Demander le remboursement'), css_class='btn btn-warning btn-lg w-100')
        )