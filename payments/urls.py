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
    
    # Paiements mobiles
    path('mobile/status/', views.MobilePaymentStatusView.as_view(), name='mobile_payment_status'),
    
    # API
    path('api/create-intent/', views.api_create_payment_intent, name='api_create_intent'),
    path('api/mobile-payment/', views.api_initiate_mobile_payment, name='api_mobile_payment'),
    path('api/mobile-status/<str:transaction_id>/', views.api_check_mobile_payment, name='api_mobile_status'),
    path('api/wallet-payment/', views.api_wallet_payment, name='api_wallet_payment'),
    path('api/wallet-balance/', views.api_wallet_balance, name='api_wallet_balance'),
    path('api/wallet-topup/', views.api_wallet_topup, name='api_wallet_topup'),
    path('api/payment-methods/', views.api_payment_methods, name='api_payment_methods'),
    path('api/payment-history/', views.api_payment_history, name='api_payment_history'),
    
    # Simulation (dev uniquement)
    path('simulate/<str:transaction_id>/', views.simulate_mobile_payment, name='simulate_mobile'),
]