"""
Commande Django pour créer des données de test pour GourmetGuide.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import random

from accounts.models import CustomUser, UserProfile
from restaurants.models import Restaurant, Category, MenuItem
from core.models import City, Country

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de test pour GourmetGuide'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données existantes avant de créer les nouvelles'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des données existantes...')
            self.clear_data()

        self.stdout.write('Création des données de test...')
        
        # Créer les données dans l'ordre des dépendances
        self.create_countries_and_cities()
        self.create_categories()
        self.create_users()
        self.create_restaurants()
        self.create_menu_items()
        self.create_sample_admin()
        
        self.stdout.write(
            self.style.SUCCESS('Données de test créées avec succès!')
        )

    def clear_data(self):
        """Supprimer les données existantes."""
        MenuItem.objects.all().delete()
        Restaurant.objects.all().delete()
        Category.objects.all().delete()
        UserProfile.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()
        City.objects.all().delete()
        Country.objects.all().delete()

    def create_countries_and_cities(self):
        """Créer les pays et villes."""
        self.stdout.write('Création des pays et villes...')
        
        # Togo
        country, created = Country.objects.get_or_create(
            name='Togo',
            defaults={
                'code': 'TG',
                'is_active': True
            }
        )
        
        # Lomé
        City.objects.get_or_create(
            name='Lomé',
            defaults={
                'country': country,
                'latitude': 6.1319,
                'longitude': 1.2228,
                'is_active': True
            }
        )

    def create_categories(self):
        """Créer les catégories de cuisine."""
        self.stdout.write('Création des catégories...')
        
        categories_data = [
            {'name': 'Cuisine Locale', 'description': 'Plats traditionnels togolais'},
            {'name': 'Cuisine Française', 'description': 'Cuisine française traditionnelle'},
            {'name': 'Cuisine Asiatique', 'description': 'Cuisine chinoise, japonaise, thaï'},
            {'name': 'Grillades', 'description': 'Viandes grillées et barbecue'},
            {'name': 'Végétarien', 'description': 'Cuisine végétarienne et vegan'},
            {'name': 'Desserts', 'description': 'Pâtisseries et desserts'},
        ]
        
        for cat_data in categories_data:
            slug = slugify(cat_data['name'])
            Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'is_active': True
                }
            )

    def create_users(self):
        """Créer des utilisateurs de test."""
        self.stdout.write('Création des utilisateurs...')
        
        # Clients
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                email=f'client{i}@test.com',
                defaults={
                    'username': f'client{i}',
                    'first_name': f'Client',
                    'last_name': f'{i}',
                    'user_type': 'client',
                    'phone': f'+228 90 00 00 {i:02d}',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                UserProfile.objects.create(user=user)

        # Propriétaires de restaurants
        restaurant_owners = [
            {'email': 'baobab@restaurant.com', 'name': 'Baobab', 'last': 'Restaurant'},
            {'email': 'mama@restaurant.com', 'name': 'Mama', 'last': 'Africa'},
            {'email': 'pizza@restaurant.com', 'name': 'Pizza', 'last': 'Express'},
            {'email': 'gourmet@restaurant.com', 'name': 'Le', 'last': 'Gourmet'},
            {'email': 'asian@restaurant.com', 'name': 'Asian', 'last': 'Fusion'},
        ]
        
        for owner_data in restaurant_owners:
            user, created = User.objects.get_or_create(
                email=owner_data['email'],
                defaults={
                    'username': owner_data['email'].split('@')[0],
                    'first_name': owner_data['name'],
                    'last_name': owner_data['last'],
                    'user_type': 'restaurant',
                    'phone': f'+228 22 21 12 {random.randint(30, 99)}',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                UserProfile.objects.create(user=user)

        # Livreurs
        for i in range(1, 4):
            user, created = User.objects.get_or_create(
                email=f'livreur{i}@test.com',
                defaults={
                    'username': f'livreur{i}',
                    'first_name': f'Livreur',
                    'last_name': f'{i}',
                    'user_type': 'delivery',
                    'phone': f'+228 92 00 00 {i:02d}',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                UserProfile.objects.create(user=user)

    def create_restaurants(self):
        """Créer des restaurants de test."""
        self.stdout.write('Création des restaurants...')
        
        restaurants_data = [
            {
                'name': 'Restaurant Le Baobab',
                'owner_email': 'baobab@restaurant.com',
                'description': 'Cuisine africaine authentique avec des plats traditionnels togolais',
                'address': 'Avenue du 24 Janvier, Lomé',
                'phone': '+228 22 21 12 34',
                'latitude': 6.1319,
                'longitude': 1.2228,
            },
            {
                'name': 'Chez Mama Africa',
                'owner_email': 'mama@restaurant.com',
                'description': 'Spécialités africaines dans une ambiance familiale',
                'address': 'Rue de la Paix, Lomé',
                'phone': '+228 22 21 12 35',
                'latitude': 6.1280,
                'longitude': 1.2150,
            },
            {
                'name': 'Pizza Express Lomé',
                'owner_email': 'pizza@restaurant.com',
                'description': 'Pizzas fraîches et livraison rapide',
                'address': 'Boulevard Gnassingbé Eyadéma, Lomé',
                'phone': '+228 22 21 12 36',
                'latitude': 6.1350,
                'longitude': 1.2300,
            },
            {
                'name': 'Le Gourmet Français',
                'owner_email': 'gourmet@restaurant.com',
                'description': 'Cuisine française raffinée',
                'address': 'Avenue Sarakawa, Lomé',
                'phone': '+228 22 21 12 37',
                'latitude': 6.1400,
                'longitude': 1.2100,
            },
            {
                'name': 'Asian Fusion',
                'owner_email': 'asian@restaurant.com',
                'description': 'Cuisine asiatique moderne',
                'address': 'Rue de Kénu, Lomé',
                'phone': '+228 22 21 12 38',
                'latitude': 6.1250,
                'longitude': 1.2380,
            },
        ]
        
        for resto_data in restaurants_data:
            try:
                owner = User.objects.get(email=resto_data['owner_email'])
                slug = slugify(resto_data['name'])
                restaurant, created = Restaurant.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'owner': owner,
                        'name': resto_data['name'],
                        'description': resto_data['description'],
                        'address': resto_data['address'],
                        'city': 'Lomé',
                        'phone': resto_data['phone'],
                        'latitude': resto_data['latitude'],
                        'longitude': resto_data['longitude'],
                        'delivery_fee': Decimal('500.00'),
                        'min_order_amount': Decimal('2000.00'),
                        'status': 'active',
                        'average_rating': round(random.uniform(3.5, 5.0), 1),
                        'total_reviews': random.randint(10, 100),
                        'opening_hours': {
                            'monday': {'open': '08:00', 'close': '22:00'},
                            'tuesday': {'open': '08:00', 'close': '22:00'},
                            'wednesday': {'open': '08:00', 'close': '22:00'},
                            'thursday': {'open': '08:00', 'close': '22:00'},
                            'friday': {'open': '08:00', 'close': '23:00'},
                            'saturday': {'open': '08:00', 'close': '23:00'},
                            'sunday': {'open': '10:00', 'close': '22:00'},
                        }
                    }
                )
                
                if created:
                    # Assigner des catégories
                    categories = Category.objects.all()
                    if categories:
                        restaurant.categories.set(random.sample(list(categories), min(2, len(categories))))
                    
                    self.stdout.write(f'Restaurant créé: {restaurant.name}')
                else:
                    self.stdout.write(f'Restaurant existant: {restaurant.name}')
                    
            except User.DoesNotExist:
                self.stdout.write(f'Propriétaire non trouvé pour: {resto_data["owner_email"]}')

    def create_menu_items(self):
        """Créer des éléments de menu."""
        self.stdout.write('Création des éléments de menu...')
        
        menu_items_data = [
            # Items pour Restaurant Le Baobab
            {'restaurant_slug': 'restaurant-le-baobab', 'name': 'Fufu aux légumes', 'price': '1500.00', 'category': 'main'},
            {'restaurant_slug': 'restaurant-le-baobab', 'name': 'Riz jollof', 'price': '2000.00', 'category': 'main'},
            {'restaurant_slug': 'restaurant-le-baobab', 'name': 'Poisson grillé', 'price': '2500.00', 'category': 'main'},
            
            # Items pour Chez Mama Africa
            {'restaurant_slug': 'chez-mama-africa', 'name': 'Attieké poisson', 'price': '1800.00', 'category': 'main'},
            {'restaurant_slug': 'chez-mama-africa', 'name': 'Banku', 'price': '1200.00', 'category': 'main'},
            
            # Items pour Pizza Express
            {'restaurant_slug': 'pizza-express-lome', 'name': 'Pizza Margherita', 'price': '3000.00', 'category': 'main'},
            {'restaurant_slug': 'pizza-express-lome', 'name': 'Pizza 4 Fromages', 'price': '3500.00', 'category': 'main'},
            
            # Items pour Le Gourmet Français
            {'restaurant_slug': 'le-gourmet-francais', 'name': 'Coq au vin', 'price': '4500.00', 'category': 'main'},
            {'restaurant_slug': 'le-gourmet-francais', 'name': 'Ratatouille', 'price': '3000.00', 'category': 'main'},
            
            # Items pour Asian Fusion
            {'restaurant_slug': 'asian-fusion', 'name': 'Pad Thai', 'price': '2800.00', 'category': 'main'},
            {'restaurant_slug': 'asian-fusion', 'name': 'Sushi Mix', 'price': '4000.00', 'category': 'main'},
        ]
        
        for item_data in menu_items_data:
            try:
                restaurant = Restaurant.objects.get(slug=item_data['restaurant_slug'])
                slug = slugify(f"{restaurant.name}-{item_data['name']}")
                
                MenuItem.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'restaurant': restaurant,
                        'name': item_data['name'],
                        'description': f'Délicieux {item_data["name"]} préparé avec soin',
                        'category': item_data['category'],
                        'price': Decimal(item_data['price']),
                        'is_available': True,
                    }
                )
                self.stdout.write(f'Menu item créé: {item_data["name"]} pour {restaurant.name}')
                
            except Restaurant.DoesNotExist:
                self.stdout.write(f'Restaurant non trouvé: {item_data["restaurant_slug"]}')

    def create_sample_admin(self):
        """Créer un utilisateur admin pour les tests."""
        if not User.objects.filter(email='admin@gourmetguide.com').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@gourmetguide.com',
                password='admin123',
                first_name='Admin',
                last_name='GourmetGuide',
                user_type='admin'
            )
            UserProfile.objects.create(user=admin_user)
            self.stdout.write('Utilisateur admin créé: admin@gourmetguide.com / admin123')