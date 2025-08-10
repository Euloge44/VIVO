"""
Context processors pour GourmetGuide.
"""

from django.conf import settings
from .models import SiteSettings


def site_settings(request):
    """
    Ajoute les paramètres du site au contexte des templates.
    """
    try:
        site_config = SiteSettings.get_settings()
        return {
            'site_settings': site_config,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
            'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        }
    except Exception:
        return {
            'site_settings': None,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
            'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        }