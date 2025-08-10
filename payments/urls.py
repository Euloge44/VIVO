"""
URLs pour l'application payments.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Processus de paiement
    path('process/', views.ProcessPaymentView.as_view(), name='process'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='cancel'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # Portefeuille
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('wallet/topup/', views.WalletTopUpView.as_view(), name='wallet_topup'),
    
    # API endpoints
    path('api/process/', views.api_process_payment, name='api_process'),
    path('api/methods/', views.api_payment_methods, name='api_methods'),
    path('api/wallet/', views.api_wallet, name='api_wallet'),
    path('api/mobile-pay/', views.api_mobile_payment, name='api_mobile_payment'),
]