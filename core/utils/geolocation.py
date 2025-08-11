"""
Utilitaires de géolocalisation pour GourmetGuide.
"""

import math
import requests
from decimal import Decimal
from typing import Tuple, List, Dict, Optional
from django.conf import settings
from django.core.cache import cache


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance entre deux points géographiques en utilisant la formule de Haversine.
    
    Args:
        lat1, lon1: Coordonnées du premier point
        lat2, lon2: Coordonnées du deuxième point
    
    Returns:
        Distance en kilomètres
    """
    # Convertir en radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Formule de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en kilomètres
    r = 6371
    
    return c * r


def get_restaurants_within_radius(
    user_lat: float, 
    user_lon: float, 
    radius_km: float = 10
) -> List[Dict]:
    """
    Trouve les restaurants dans un rayon donné autour d'une position.
    
    Args:
        user_lat: Latitude de l'utilisateur
        user_lon: Longitude de l'utilisateur
        radius_km: Rayon de recherche en kilomètres
    
    Returns:
        Liste des restaurants avec leur distance
    """
    from restaurants.models import Restaurant
    
    restaurants = []
    
    for restaurant in Restaurant.objects.filter(status='active'):
        if restaurant.latitude and restaurant.longitude:
            distance = calculate_distance(
                user_lat, user_lon,
                float(restaurant.latitude), float(restaurant.longitude)
            )
            
            if distance <= radius_km:
                restaurants.append({
                    'restaurant': restaurant,
                    'distance': round(distance, 2)
                })
    
    # Trier par distance
    restaurants.sort(key=lambda x: x['distance'])
    
    return restaurants


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convertit une adresse en coordonnées géographiques via Google Maps API.
    
    Args:
        address: Adresse à géocoder
    
    Returns:
        Tuple (latitude, longitude) ou None si échec
    """
    if not hasattr(settings, 'GOOGLE_MAPS_API_KEY') or not settings.GOOGLE_MAPS_API_KEY:
        return None
    
    # Vérifier le cache
    cache_key = f"geocode_{address.replace(' ', '_').lower()}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': settings.GOOGLE_MAPS_API_KEY,
            'region': 'TG'  # Biais vers le Togo
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            result = (location['lat'], location['lng'])
            
            # Mettre en cache pour 24h
            cache.set(cache_key, result, 86400)
            
            return result
            
    except Exception as e:
        print(f"Erreur de géocodage: {e}")
    
    return None


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Convertit des coordonnées en adresse via Google Maps API.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Adresse formatée ou None si échec
    """
    if not hasattr(settings, 'GOOGLE_MAPS_API_KEY') or not settings.GOOGLE_MAPS_API_KEY:
        return None
    
    # Vérifier le cache
    cache_key = f"reverse_geocode_{lat}_{lon}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lon}",
            'key': settings.GOOGLE_MAPS_API_KEY,
            'region': 'TG'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            address = data['results'][0]['formatted_address']
            
            # Mettre en cache pour 24h
            cache.set(cache_key, address, 86400)
            
            return address
            
    except Exception as e:
        print(f"Erreur de géocodage inverse: {e}")
    
    return None


def get_delivery_zones(restaurant_lat: float, restaurant_lon: float, radius: int) -> List[Dict]:
    """
    Génère les zones de livraison pour un restaurant.
    
    Args:
        restaurant_lat: Latitude du restaurant
        restaurant_lon: Longitude du restaurant
        radius: Rayon de livraison en kilomètres
    
    Returns:
        Liste des zones avec coordonnées pour affichage sur carte
    """
    zones = []
    
    # Créer des cercles concentriques pour les zones de livraison
    for i in range(1, radius + 1, 2):
        zone = {
            'center': {'lat': restaurant_lat, 'lng': restaurant_lon},
            'radius': i * 1000,  # Convertir en mètres
            'color': f'rgba(102, 126, 234, {0.3 - (i * 0.05)})',
            'delivery_fee': calculate_delivery_fee(i)
        }
        zones.append(zone)
    
    return zones


def calculate_delivery_fee(distance_km: float) -> Decimal:
    """
    Calcule les frais de livraison basés sur la distance.
    
    Args:
        distance_km: Distance en kilomètres
    
    Returns:
        Frais de livraison en FCFA
    """
    base_fee = Decimal('500')  # Frais de base
    
    if distance_km <= 3:
        return base_fee
    elif distance_km <= 5:
        return base_fee + Decimal('200')
    elif distance_km <= 10:
        return base_fee + Decimal('500')
    else:
        return base_fee + Decimal('1000')


def find_optimal_delivery_route(delivery_person_location: Tuple[float, float], 
                               orders: List[Dict]) -> List[Dict]:
    """
    Trouve la route optimale pour un livreur avec plusieurs commandes.
    
    Args:
        delivery_person_location: Position actuelle du livreur
        orders: Liste des commandes avec coordonnées de livraison
    
    Returns:
        Liste des commandes ordonnées pour une route optimale
    """
    if not orders:
        return []
    
    # Algorithme simple du plus proche voisin
    current_location = delivery_person_location
    remaining_orders = orders.copy()
    optimized_route = []
    
    while remaining_orders:
        closest_order = None
        min_distance = float('inf')
        
        for order in remaining_orders:
            distance = calculate_distance(
                current_location[0], current_location[1],
                order['delivery_lat'], order['delivery_lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_order = order
        
        if closest_order:
            closest_order['distance_from_current'] = round(min_distance, 2)
            optimized_route.append(closest_order)
            remaining_orders.remove(closest_order)
            current_location = (closest_order['delivery_lat'], closest_order['delivery_lon'])
    
    return optimized_route


def get_nearby_landmarks(lat: float, lon: float, radius: int = 1000) -> List[Dict]:
    """
    Trouve les points d'intérêt près d'une position via Google Places API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Rayon de recherche en mètres
    
    Returns:
        Liste des points d'intérêt
    """
    if not hasattr(settings, 'GOOGLE_MAPS_API_KEY') or not settings.GOOGLE_MAPS_API_KEY:
        return []
    
    cache_key = f"landmarks_{lat}_{lon}_{radius}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lon}",
            'radius': radius,
            'type': 'point_of_interest',
            'key': settings.GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        landmarks = []
        if data['status'] == 'OK':
            for place in data.get('results', []):
                landmark = {
                    'name': place.get('name'),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'types': place.get('types', []),
                    'rating': place.get('rating'),
                    'vicinity': place.get('vicinity')
                }
                landmarks.append(landmark)
        
        # Mettre en cache pour 1 heure
        cache.set(cache_key, landmarks, 3600)
        
        return landmarks
        
    except Exception as e:
        print(f"Erreur lors de la recherche de landmarks: {e}")
        return []


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Valide des coordonnées géographiques.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        True si les coordonnées sont valides
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def get_togo_bounds() -> Dict[str, float]:
    """
    Retourne les limites géographiques du Togo.
    
    Returns:
        Dictionnaire avec les limites nord, sud, est, ouest
    """
    return {
        'north': 11.1395,
        'south': 6.1041,
        'east': 1.8067,
        'west': -0.1495
    }


def is_location_in_togo(lat: float, lon: float) -> bool:
    """
    Vérifie si une position est au Togo.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        True si la position est au Togo
    """
    bounds = get_togo_bounds()
    return (bounds['south'] <= lat <= bounds['north'] and 
            bounds['west'] <= lon <= bounds['east'])