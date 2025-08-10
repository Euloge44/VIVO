"""
Commande Django pour créer des données de test pour GourmetGuide.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
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
        
        # Créer les données de base
        self.create_countries_and_cities()
        self.create_categories()
        self.create_users()
        self.create_restaurants()
        self.create_menu_items()
        
        self.stdout.write(
            self.style.SUCCESS('Données de test créées avec succès !')
        )
    
    def clear_data(self):
        """Supprimer les données existantes."""
        MenuItem.objects.all().delete()
        Restaurant.objects.all().delete()
        Category.objects.all().delete()
        City.objects.all().delete()
        Country.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
    
    def create_countries_and_cities(self):
        """Créer les pays et villes."""
        self.stdout.write('Création des pays et villes...')
        
        togo, created = Country.objects.get_or_create(
            name='Togo',
            defaults={'code': 'TG', 'is_active': True}
        )
        
        cities_data = [
            {'name': 'Lomé', 'latitude': 6.1319, 'longitude': 1.2228},
            {'name': 'Kara', 'latitude': 9.5511, 'longitude': 1.1864},
            {'name': 'Sokodé', 'latitude': 8.9833, 'longitude': 1.1333},
            {'name': 'Kpalimé', 'latitude': 6.9000, 'longitude': 0.6333},
        ]
        
        for city_data in cities_data:
            City.objects.get_or_create(
                name=city_data['name'],
                country=togo,
                defaults={
                    'latitude': city_data['latitude'],
                    'longitude': city_data['longitude'],
                    'is_active': True
                }
            )
    
    def create_categories(self):
        """Créer les catégories de restaurants."""
        self.stdout.write('Création des catégories...')
        
        categories_data = [
            {'name': 'Cuisine Africaine', 'description': 'Plats traditionnels africains'},
            {'name': 'Fast Food', 'description': 'Restauration rapide'},
            {'name': 'Pizza', 'description': 'Pizzerias'},
            {'name': 'Cuisine Française', 'description': 'Cuisine française traditionnelle'},
            {'name': 'Cuisine Asiatique', 'description': 'Cuisine chinoise, japonaise, thaï'},
            {'name': 'Grillades', 'description': 'Viandes grillées et barbecue'},
            {'name': 'Végétarien', 'description': 'Cuisine végétarienne et vegan'},
            {'name': 'Desserts', 'description': 'Pâtisseries et desserts'},
        ]
        
        for cat_data in categories_data:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
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
                    'first_name': f'Client{i}',
                    'last_name': 'Test',
                    'user_type': 'client',
                    'phone': f'+228 90 00 00 {i:02d}',
                    'address': f'Quartier Test {i}, Lomé',
                    'city': 'Lomé',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                UserProfile.objects.create(user=user)
        
        # Restaurateurs
        restaurant_owners = [
            {'name': 'Restaurant Le Baobab', 'owner': 'baobab'},
            {'name': 'Chez Mama Africa', 'owner': 'mama'},
            {'name': 'Pizza Express Lomé', 'owner': 'pizza'},
            {'name': 'Le Gourmet Français', 'owner': 'gourmet'},
            {'name': 'Asian Fusion', 'owner': 'asian'},
        ]
        
        for resto_data in restaurant_owners:
            user, created = User.objects.get_or_create(
                email=f'{resto_data["owner"]}@restaurant.com',
                defaults={
                    'username': resto_data['owner'],
                    'first_name': resto_data['name'].split()[0],
                    'last_name': 'Restaurant',
                    'user_type': 'restaurant',
                    'phone': f'+228 91 00 00 {random.randint(10, 99)}',
                    'address': f'Avenue Test, Lomé',
                    'city': 'Lomé',
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
                    'first_name': f'Livreur{i}',
                    'last_name': 'Test',
                    'user_type': 'delivery',
                    'phone': f'+228 92 00 00 {i:02d}',
                    'address': f'Quartier Livreur {i}, Lomé',
                    'city': 'Lomé',
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
                'cuisine_type': 'Africaine',
                'address': 'Avenue du 24 Janvier, Lomé',
                'phone': '+228 22 21 12 34',
                'latitude': 6.1319,
                'longitude': 1.2228,
                'price_range': 'moderate',
            },
            {
                'name': 'Chez Mama Africa',
                'owner_email': 'mama@restaurant.com',
                'description': 'Spécialités africaines dans une ambiance familiale',
                'cuisine_type': 'Africaine',
                'address': 'Rue de la Paix, Lomé',
                'phone': '+228 22 21 12 35',
                'latitude': 6.1280,
                'longitude': 1.2150,
                'price_range': 'budget',
            },
            {
                'name': 'Pizza Express Lomé',
                'owner_email': 'pizza@restaurant.com',
                'description': 'Pizzas fraîches et livraison rapide',
                'cuisine_type': 'Italienne',
                'address': 'Boulevard Gnassingbé Eyadéma, Lomé',
                'phone': '+228 22 21 12 36',
                'latitude': 6.1350,
                'longitude': 1.2300,
                'price_range': 'moderate',
            },
            {
                'name': 'Le Gourmet Français',
                'owner_email': 'gourmet@restaurant.com',
                'description': 'Cuisine française raffinée',
                'cuisine_type': 'Française',
                'address': 'Avenue Sarakawa, Lomé',
                'phone': '+228 22 21 12 37',
                'latitude': 6.1400,
                'longitude': 1.2100,
                'price_range': 'expensive',
            },
            {
                'name': 'Asian Fusion',
                'owner_email': 'asian@restaurant.com',
                'description': 'Cuisine asiatique moderne',
                'cuisine_type': 'Asiatique',
                'address': 'Rue de Kénu, Lomé',
                'phone': '+228 22 21 12 38',
                'latitude': 6.1250,
                'longitude': 1.2380,
                'price_range': 'moderate',
            },
        ]
        
        for resto_data in restaurants_data:
            try:
                owner = User.objects.get(email=resto_data['owner_email'])
                restaurant, created = Restaurant.objects.get_or_create(
                    owner=owner,
                    defaults={
                        'name': resto_data['name'],
                        'description': resto_data['description'],
                        'cuisine_type': resto_data['cuisine_type'],
                        'address': resto_data['address'],
                        'city': 'Lomé',
                        'phone': resto_data['phone'],
                        'latitude': resto_data['latitude'],
                        'longitude': resto_data['longitude'],
                        'price_range': resto_data['price_range'],
                        'delivery_fee': Decimal('500.00'),
                        'minimum_order': Decimal('2000.00'),
                        'estimated_delivery_time': 30,
                        'is_active': True,
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
                        restaurant.categories.add(random.choice(categories))
                
            except User.DoesNotExist:
                self.stdout.write(f'Utilisateur {resto_data["owner_email"]} non trouvé')
    
    def create_menu_items(self):
        """Créer des articles de menu."""
        self.stdout.write('Création des articles de menu...')
        
        restaurants = Restaurant.objects.all()
        categories = Category.objects.all()
        
        menu_items_data = [
            # Cuisine Africaine
            {'name': 'Fufu aux légumes', 'price': 1500, 'category': 'Cuisine Africaine'},
            {'name': 'Riz jollof', 'price': 2000, 'category': 'Cuisine Africaine'},
            {'name': 'Poulet DG', 'price': 3500, 'category': 'Cuisine Africaine'},
            {'name': 'Poisson braisé', 'price': 2500, 'category': 'Cuisine Africaine'},
            {'name': 'Banku aux légumes', 'price': 1800, 'category': 'Cuisine Africaine'},
            
            # Fast Food
            {'name': 'Burger Classique', 'price': 2500, 'category': 'Fast Food'},
            {'name': 'Frites', 'price': 1000, 'category': 'Fast Food'},
            {'name': 'Nuggets de poulet', 'price': 2000, 'category': 'Fast Food'},
            {'name': 'Sandwich club', 'price': 2200, 'category': 'Fast Food'},
            
            # Pizza
            {'name': 'Pizza Margherita', 'price': 3000, 'category': 'Pizza'},
            {'name': 'Pizza 4 Fromages', 'price': 3500, 'category': 'Pizza'},
            {'name': 'Pizza Végétarienne', 'price': 3200, 'category': 'Pizza'},
            {'name': 'Pizza Spéciale', 'price': 4000, 'category': 'Pizza'},
        ]
        
        for restaurant in restaurants:
            # Créer 5-10 articles par restaurant
            num_items = random.randint(5, 10)
            selected_items = random.sample(menu_items_data, min(num_items, len(menu_items_data)))
            
            for item_data in selected_items:
                try:
                    category = categories.filter(name__icontains=item_data['category']).first()
                    
                    MenuItem.objects.get_or_create(
                        restaurant=restaurant,
                        name=item_data['name'],
                        defaults={
                            'description': f"Délicieux {item_data['name'].lower()} préparé avec soin",
                            'price': Decimal(str(item_data['price'])),
                            'category': category,
                            'preparation_time': random.randint(10, 30),
                            'calories': random.randint(200, 800),
                            'is_vegetarian': 'végé' in item_data['name'].lower() or 'légumes' in item_data['name'].lower(),
                            'is_vegan': False,
                            'is_available': True,
                            'order': random.randint(1, 100),
                        }
                    )
                except Exception as e:
                    self.stdout.write(f'Erreur lors de la création de {item_data["name"]}: {e}')
    
    def create_sample_admin(self):
        """Créer un utilisateur admin de test."""
        admin_user, created = User.objects.get_or_create(
            email='admin@gourmetguide.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'GourmetGuide',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.create(user=admin_user)