"""
URLs pour l'application loyalty.
"""

from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    # Programme de fidélité
    path('', views.LoyaltyDashboardView.as_view(), name='dashboard'),
    path('card/', views.LoyaltyCardView.as_view(), name='card'),
    path('rewards/', views.RewardsView.as_view(), name='rewards'),
    path('redeem/<int:reward_id>/', views.RedeemRewardView.as_view(), name='redeem'),
    path('history/', views.PointHistoryView.as_view(), name='history'),
    
    # Programme de parrainage
    path('referral/', views.ReferralProgramView.as_view(), name='referral'),
    
    # API endpoints
    path('api/card/', views.api_loyalty_card, name='api_card'),
    path('api/points/', views.api_points_balance, name='api_points'),
    path('api/rewards/', views.api_available_rewards, name='api_rewards'),
    path('api/redeem/', views.api_redeem_reward, name='api_redeem'),
    path('api/history/', views.api_point_history, name='api_history'),
]