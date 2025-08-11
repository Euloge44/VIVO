"""
gourmetguide URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),
    
    # APIs (sans préfixe de langue)
    path('api/auth/', include('accounts.api_urls')),
    path('api/restaurants/', include('restaurants.api_urls')),
    path('api/orders/', include('orders.api_urls')),
    
    # DRF browsable API
    path('api-auth/', include('rest_framework.urls')),
]

# URLs avec support multilingue
urlpatterns += i18n_patterns(
    # Application principale
    path('', include('core.urls')),
    
    # Authentification
    path('accounts/', include('accounts.urls')),
    
    # Applications principales
    path('restaurants/', include('restaurants.urls')),
    path('orders/', include('orders.urls')),
    path('delivery/', include('delivery.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('loyalty/', include('loyalty.urls')),
    path('notifications/', include('notifications.urls')),
    path('analytics/', include('analytics.urls')),
    
    # Authentification sociale (allauth)
    path('auth/', include('allauth.urls')),
    
    prefix_default_language=False
)

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
