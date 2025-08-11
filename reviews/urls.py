"""
URLs pour l'application reviews.
"""

from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Gestion des avis
    path('', views.ReviewListView.as_view(), name='list'),
    path('create/', views.ReviewCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete'),
    
    # Actions sur les avis
    path('<int:pk>/helpful/', views.MarkReviewHelpfulView.as_view(), name='helpful'),
    path('<int:pk>/report/', views.ReportReviewView.as_view(), name='report'),
    
    # API endpoints
    path('api/list/', views.api_review_list, name='api_list'),
    path('api/create/', views.api_review_create, name='api_create'),
    path('api/<int:pk>/', views.api_review_detail, name='api_detail'),
    path('api/<int:pk>/helpful/', views.api_mark_helpful, name='api_helpful'),
]