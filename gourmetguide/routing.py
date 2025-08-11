"""
Configuration de routage WebSocket pour GourmetGuide.
"""

from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from notifications.consumers import (
    NotificationConsumer, 
    OrderTrackingConsumer, 
    RestaurantConsumer, 
    DeliveryConsumer
)

websocket_urlpatterns = [
    # Notifications utilisateur
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    
    # Suivi de commandes
    re_path(r'ws/orders/(?P<order_id>[0-9a-f-]+)/track/$', OrderTrackingConsumer.as_asgi()),
    
    # Notifications restaurant
    re_path(r'ws/restaurant/$', RestaurantConsumer.as_asgi()),
    
    # Interface livreur
    re_path(r'ws/delivery/$', DeliveryConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})