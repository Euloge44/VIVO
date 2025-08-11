"""
Consumers WebSocket pour les notifications en temps réel.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications utilisateur."""
    
    async def connect(self):
        """Connexion WebSocket."""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Groupe de notifications pour cet utilisateur
        self.notification_group_name = f"notifications_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les notifications non lues
        await self.send_unread_notifications()
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du client."""
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            
            if action == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                await self.mark_notification_read(notification_id)
            
            elif action == 'mark_all_read':
                await self.mark_all_notifications_read()
            
            elif action == 'get_unread_count':
                await self.send_unread_count()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
    
    async def send_unread_notifications(self):
        """Envoyer les notifications non lues."""
        notifications = await self.get_unread_notifications()
        
        for notification in notifications:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'created_at': notification.created_at.isoformat(),
                    'data': notification.data
                }
            }))
    
    async def send_unread_count(self):
        """Envoyer le nombre de notifications non lues."""
        count = await self.get_unread_count()
        
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    async def notification_message(self, event):
        """Recevoir une notification du groupe."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def notification_update(self, event):
        """Recevoir une mise à jour de notification."""
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'notification_id': event['notification_id'],
            'action': event['action']
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Récupérer les notifications non lues."""
        return list(
            Notification.objects.filter(
                user=self.user,
                is_read=False
            ).order_by('-created_at')[:10]
        )
    
    @database_sync_to_async
    def get_unread_count(self):
        """Compter les notifications non lues."""
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marquer une notification comme lue."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Marquer toutes les notifications comme lues."""
        count = Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return count


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    """Consumer pour le suivi des commandes en temps réel."""
    
    async def connect(self):
        """Connexion WebSocket."""
        self.user = self.scope["user"]
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Vérifier que l'utilisateur peut accéder à cette commande
        if not await self.can_access_order():
            await self.close()
            return
        
        # Groupe de suivi pour cette commande
        self.order_group_name = f"order_tracking_{self.order_id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.order_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer le statut actuel
        await self.send_current_order_status()
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        if hasattr(self, 'order_group_name'):
            await self.channel_layer.group_discard(
                self.order_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du client."""
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            
            if action == 'get_status':
                await self.send_current_order_status()
            
            elif action == 'update_location' and await self.is_delivery_person():
                # Mise à jour de position du livreur
                lat = text_data_json.get('lat')
                lng = text_data_json.get('lng')
                await self.update_delivery_location(lat, lng)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
    
    async def send_current_order_status(self):
        """Envoyer le statut actuel de la commande."""
        order_data = await self.get_order_data()
        
        if order_data:
            await self.send(text_data=json.dumps({
                'type': 'order_status',
                'order': order_data
            }))
    
    async def order_status_update(self, event):
        """Recevoir une mise à jour de statut de commande."""
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order': event['order_data']
        }))
    
    async def delivery_location_update(self, event):
        """Recevoir une mise à jour de position du livreur."""
        await self.send(text_data=json.dumps({
            'type': 'delivery_location',
            'location': event['location']
        }))
    
    @database_sync_to_async
    def can_access_order(self):
        """Vérifier si l'utilisateur peut accéder à cette commande."""
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=self.order_id)
            
            # Client propriétaire de la commande
            if order.user == self.user:
                return True
            
            # Propriétaire du restaurant
            if (self.user.user_type == 'restaurant' and 
                order.restaurant.owner == self.user):
                return True
            
            # Livreur assigné
            if (self.user.user_type == 'livreur' and 
                hasattr(order, 'delivery') and 
                order.delivery.delivery_person.user == self.user):
                return True
            
            # Admin
            if self.user.is_staff:
                return True
                
        except Order.DoesNotExist:
            pass
        
        return False
    
    @database_sync_to_async
    def is_delivery_person(self):
        """Vérifier si l'utilisateur est un livreur."""
        return self.user.user_type == 'livreur'
    
    @database_sync_to_async
    def get_order_data(self):
        """Récupérer les données de la commande."""
        from orders.models import Order
        
        try:
            order = Order.objects.select_related(
                'restaurant', 'user'
            ).prefetch_related('items__menu_item').get(id=self.order_id)
            
            # Données de base
            order_data = {
                'id': str(order.id),
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'restaurant': {
                    'name': order.restaurant.name,
                    'phone': order.restaurant.phone,
                    'address': order.restaurant.address
                }
            }
            
            # Ajouter les informations de livraison si disponibles
            if hasattr(order, 'delivery') and order.delivery:
                delivery = order.delivery
                order_data['delivery'] = {
                    'status': delivery.status,
                    'estimated_time': delivery.estimated_delivery_time.isoformat() if delivery.estimated_delivery_time else None,
                    'delivery_person': {
                        'name': delivery.delivery_person.user.get_full_name(),
                        'phone': delivery.delivery_person.user.phone
                    } if delivery.delivery_person else None
                }
                
                # Position du livreur si disponible
                if (delivery.delivery_person and 
                    delivery.delivery_person.current_latitude and 
                    delivery.delivery_person.current_longitude):
                    order_data['delivery']['location'] = {
                        'lat': float(delivery.delivery_person.current_latitude),
                        'lng': float(delivery.delivery_person.current_longitude),
                        'updated_at': delivery.delivery_person.location_updated_at.isoformat()
                    }
            
            return order_data
            
        except Order.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_delivery_location(self, lat, lng):
        """Mettre à jour la position du livreur."""
        from delivery.models import DeliveryPerson
        
        try:
            delivery_person = DeliveryPerson.objects.get(user=self.user)
            delivery_person.current_latitude = lat
            delivery_person.current_longitude = lng
            delivery_person.location_updated_at = timezone.now()
            delivery_person.save()
            
            return True
        except DeliveryPerson.DoesNotExist:
            return False


class RestaurantConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications des restaurants."""
    
    async def connect(self):
        """Connexion WebSocket."""
        self.user = self.scope["user"]
        
        if (self.user.is_anonymous or 
            self.user.user_type != 'restaurant'):
            await self.close()
            return
        
        # Groupe pour ce restaurant
        restaurant_id = await self.get_restaurant_id()
        if not restaurant_id:
            await self.close()
            return
        
        self.restaurant_group_name = f"restaurant_{restaurant_id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.restaurant_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        if hasattr(self, 'restaurant_group_name'):
            await self.channel_layer.group_discard(
                self.restaurant_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du client."""
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            
            if action == 'update_order_status':
                order_id = text_data_json.get('order_id')
                new_status = text_data_json.get('status')
                await self.update_order_status(order_id, new_status)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
    
    async def new_order(self, event):
        """Recevoir une nouvelle commande."""
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order': event['order_data']
        }))
    
    async def order_update(self, event):
        """Recevoir une mise à jour de commande."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order': event['order_data']
        }))
    
    @database_sync_to_async
    def get_restaurant_id(self):
        """Récupérer l'ID du restaurant de l'utilisateur."""
        from restaurants.models import Restaurant
        
        try:
            restaurant = Restaurant.objects.get(owner=self.user)
            return restaurant.id
        except Restaurant.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_order_status(self, order_id, new_status):
        """Mettre à jour le statut d'une commande."""
        from orders.models import Order
        
        try:
            order = Order.objects.get(
                id=order_id,
                restaurant__owner=self.user
            )
            
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Notifier le client
            self.notify_order_status_change(order, old_status, new_status)
            
            return True
            
        except Order.DoesNotExist:
            return False


class DeliveryConsumer(AsyncWebsocketConsumer):
    """Consumer pour les livreurs."""
    
    async def connect(self):
        """Connexion WebSocket."""
        self.user = self.scope["user"]
        
        if (self.user.is_anonymous or 
            self.user.user_type != 'livreur'):
            await self.close()
            return
        
        # Groupe pour ce livreur
        self.delivery_group_name = f"delivery_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.delivery_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Marquer le livreur comme en ligne
        await self.set_delivery_person_online(True)
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        if hasattr(self, 'delivery_group_name'):
            await self.channel_layer.group_discard(
                self.delivery_group_name,
                self.channel_name
            )
        
        # Marquer le livreur comme hors ligne
        await self.set_delivery_person_online(False)
    
    async def receive(self, text_data):
        """Recevoir un message du client."""
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            
            if action == 'update_location':
                lat = text_data_json.get('lat')
                lng = text_data_json.get('lng')
                await self.update_location(lat, lng)
            
            elif action == 'accept_delivery':
                order_id = text_data_json.get('order_id')
                await self.accept_delivery(order_id)
            
            elif action == 'update_delivery_status':
                order_id = text_data_json.get('order_id')
                status = text_data_json.get('status')
                await self.update_delivery_status(order_id, status)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
    
    async def new_delivery_request(self, event):
        """Recevoir une nouvelle demande de livraison."""
        await self.send(text_data=json.dumps({
            'type': 'new_delivery_request',
            'order': event['order_data']
        }))
    
    async def delivery_update(self, event):
        """Recevoir une mise à jour de livraison."""
        await self.send(text_data=json.dumps({
            'type': 'delivery_update',
            'delivery': event['delivery_data']
        }))
    
    @database_sync_to_async
    def set_delivery_person_online(self, is_online):
        """Marquer le livreur comme en ligne/hors ligne."""
        from delivery.models import DeliveryPerson
        
        try:
            delivery_person = DeliveryPerson.objects.get(user=self.user)
            delivery_person.is_online = is_online
            delivery_person.last_seen = timezone.now()
            delivery_person.save()
            return True
        except DeliveryPerson.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_location(self, lat, lng):
        """Mettre à jour la position du livreur."""
        from delivery.models import DeliveryPerson
        
        try:
            delivery_person = DeliveryPerson.objects.get(user=self.user)
            delivery_person.current_latitude = lat
            delivery_person.current_longitude = lng
            delivery_person.location_updated_at = timezone.now()
            delivery_person.save()
            
            # Notifier les commandes en cours
            self.broadcast_location_update(delivery_person)
            
            return True
        except DeliveryPerson.DoesNotExist:
            return False
    
    @database_sync_to_async
    def accept_delivery(self, order_id):
        """Accepter une livraison."""
        from orders.models import Order
        from delivery.models import Delivery, DeliveryPerson
        
        try:
            order = Order.objects.get(id=order_id)
            delivery_person = DeliveryPerson.objects.get(user=self.user)
            
            # Créer ou mettre à jour la livraison
            delivery, created = Delivery.objects.get_or_create(
                order=order,
                defaults={
                    'delivery_person': delivery_person,
                    'status': 'assigned'
                }
            )
            
            if not created and delivery.delivery_person != delivery_person:
                return False  # Déjà assigné à un autre livreur
            
            delivery.delivery_person = delivery_person
            delivery.status = 'assigned'
            delivery.save()
            
            # Mettre à jour le statut de la commande
            order.status = 'assigned_to_delivery'
            order.save()
            
            return True
            
        except (Order.DoesNotExist, DeliveryPerson.DoesNotExist):
            return False
    
    @database_sync_to_async
    def update_delivery_status(self, order_id, status):
        """Mettre à jour le statut de livraison."""
        from delivery.models import Delivery
        
        try:
            delivery = Delivery.objects.get(
                order_id=order_id,
                delivery_person__user=self.user
            )
            
            delivery.status = status
            delivery.save()
            
            # Mettre à jour le statut de la commande
            if status == 'picked_up':
                delivery.order.status = 'out_for_delivery'
            elif status == 'delivered':
                delivery.order.status = 'delivered'
                delivery.delivered_at = timezone.now()
            
            delivery.order.save()
            
            return True
            
        except Delivery.DoesNotExist:
            return False


# Utilitaires pour envoyer des messages

async def send_notification_to_user(user_id, notification_data):
    """Envoyer une notification à un utilisateur spécifique."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f"notifications_{user_id}",
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


async def send_order_update(order_id, order_data):
    """Envoyer une mise à jour de commande."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f"order_tracking_{order_id}",
        {
            'type': 'order_status_update',
            'order_data': order_data
        }
    )


async def send_delivery_location_update(order_id, location_data):
    """Envoyer une mise à jour de position de livraison."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f"order_tracking_{order_id}",
        {
            'type': 'delivery_location_update',
            'location': location_data
        }
    )


async def notify_new_order_to_restaurant(restaurant_id, order_data):
    """Notifier un nouveau commande au restaurant."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    
    await channel_layer.group_send(
        f"restaurant_{restaurant_id}",
        {
            'type': 'new_order',
            'order_data': order_data
        }
    )