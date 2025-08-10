"""
Routing WebSocket pour les notifications en temps réel.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/orders/(?P<order_id>[0-9a-f-]+)/$', consumers.OrderTrackingConsumer.as_asgi()),
    re_path(r'ws/delivery/(?P<delivery_person_id>\d+)/$', consumers.DeliveryTrackingConsumer.as_asgi()),
]