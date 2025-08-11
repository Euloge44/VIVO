# 🍴 GourmetGuide - Plateforme de Livraison de Repas

GourmetGuide est une application web complète de livraison de repas développée avec Django, conçue spécifiquement pour le marché africain avec support des paiements mobiles locaux.

## 🌟 Fonctionnalités Principales

### 👥 Multi-Utilisateurs
- **Clients** : Commande, suivi en temps réel, portefeuille
- **Restaurants** : Gestion menu, commandes, analytics
- **Livreurs** : Interface mobile, géolocalisation, gains
- **Administrateurs** : Dashboard complet, modération

### 💳 Système de Paiement Avancé
- **Stripe** : Paiements par carte bancaire internationaux
- **Tmoney** : Simulation du paiement mobile Togocom
- **Flooz** : Simulation du paiement mobile Moov
- **Portefeuille** : Système de crédit interne
- **Espèces** : Paiement à la livraison

### 🗺️ Géolocalisation
- **Google Maps** : Cartes interactives
- **Suivi en temps réel** : Position des livreurs
- **Calcul de distance** : Frais de livraison automatiques
- **Recherche géographique** : Restaurants à proximité

### ⚡ Temps Réel
- **WebSocket** : Notifications instantanées
- **Suivi de commandes** : Mises à jour en direct
- **Chat** : Communication restaurant-client-livreur
- **Notifications push** : Alertes importantes

### 🎨 Interface Moderne
- **Bootstrap 5** : Design responsive et moderne
- **Animations** : Transitions fluides
- **PWA Ready** : Installation sur mobile
- **Multilingue** : Français/Anglais

## 🛠️ Technologies Utilisées

### Backend
- **Django 5.2.5** : Framework web principal
- **Django REST Framework** : APIs RESTful
- **Django Channels** : WebSocket et temps réel
- **PostgreSQL** : Base de données (SQLite en dev)
- **Redis** : Cache et channel layer
- **Celery** : Tâches asynchrones

### Frontend
- **Django Templates** : Rendu côté serveur
- **Bootstrap 5** : Framework CSS
- **JavaScript ES6+** : Interactivité
- **Google Maps API** : Cartes et géolocalisation
- **WebSocket** : Temps réel côté client

### Paiements
- **Stripe** : Paiements internationaux
- **Simulateurs** : Tmoney et Flooz
- **Portefeuille virtuel** : Système interne

### Déploiement
- **Docker** : Conteneurisation
- **Docker Compose** : Orchestration
- **Nginx** : Reverse proxy
- **Gunicorn** : Serveur WSGI

## 📁 Structure du Projet

```
gourmetguide/
├── accounts/           # Authentification multi-rôles
├── analytics/          # Statistiques et rapports
├── core/              # Fonctionnalités centrales
├── delivery/          # Gestion des livraisons
├── loyalty/           # Programme de fidélité
├── notifications/     # Notifications et WebSocket
├── orders/            # Gestion des commandes
├── payments/          # Système de paiement
├── restaurants/       # Gestion des restaurants
├── reviews/           # Avis et évaluations
├── static/            # Fichiers statiques
├── templates/         # Templates Django
├── media/             # Fichiers uploadés
├── docker-compose.yml # Configuration Docker
├── Dockerfile         # Image Docker
├── requirements.txt   # Dépendances Python
└── manage.py         # Utilitaire Django
```

## 🚀 Installation et Configuration

### Prérequis
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optionnel)

### Installation Locale

1. **Cloner le projet**
```bash
git clone <repository-url>
cd gourmetguide
```

2. **Créer l'environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Base de données**
```bash
python manage.py migrate
python manage.py loaddata fixtures/*.json
python manage.py createsuperuser
```

6. **Lancer le serveur**
```bash
python manage.py runserver
```

### Installation Docker

1. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

2. **Initialiser la base de données**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata fixtures/*.json
docker-compose exec web python manage.py createsuperuser
```

## ⚙️ Configuration

### Variables d'Environnement

Créez un fichier `.env` à la racine :

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/gourmetguide

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Maps
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Sécurité
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

### APIs Externes

1. **Google Maps API**
   - Activer : Maps JavaScript API, Places API, Geocoding API
   - Configurer les restrictions de domaine

2. **Stripe**
   - Créer un compte développeur
   - Récupérer les clés de test
   - Configurer les webhooks

## 📱 Utilisation

### Pour les Clients

1. **Inscription/Connexion**
   - Créer un compte client
   - Compléter le profil

2. **Commander**
   - Parcourir les restaurants
   - Utiliser la carte interactive
   - Ajouter au panier
   - Choisir la méthode de paiement

3. **Suivi**
   - Suivre en temps réel
   - Communiquer avec le restaurant/livreur
   - Évaluer après livraison

### Pour les Restaurants

1. **Configuration**
   - Créer le profil restaurant
   - Ajouter le menu et photos
   - Configurer les zones de livraison

2. **Gestion**
   - Recevoir les commandes en temps réel
   - Mettre à jour les statuts
   - Analyser les performances

### Pour les Livreurs

1. **Inscription**
   - Créer un profil livreur
   - Ajouter véhicule et documents

2. **Livraisons**
   - Voir les commandes disponibles
   - Accepter les livraisons
   - Utiliser le GPS intégré

## 🔧 Développement

### Structure des Apps

- `accounts/` : Authentification, profils utilisateurs
- `restaurants/` : CRUD restaurants, menus, catégories
- `orders/` : Commandes, panier, workflow
- `delivery/` : Livreurs, assignments, tracking
- `payments/` : Paiements, portefeuille, transactions
- `reviews/` : Avis, évaluations, modération
- `notifications/` : Notifications, WebSocket
- `loyalty/` : Points fidélité, récompenses
- `analytics/` : Statistiques, rapports
- `core/` : Utilitaires, pages statiques

### APIs REST

Toutes les fonctionnalités sont disponibles via API REST :

```
/api/auth/          # Authentification
/api/restaurants/   # Restaurants et menus
/api/orders/        # Commandes et panier
/api/payments/      # Paiements et portefeuille
/api/delivery/      # Livraisons
/api/reviews/       # Avis
/api/notifications/ # Notifications
```

### WebSocket Endpoints

```
ws://localhost:8000/ws/notifications/           # Notifications utilisateur
ws://localhost:8000/ws/orders/{id}/track/       # Suivi de commande
ws://localhost:8000/ws/restaurant/              # Notifications restaurant
ws://localhost:8000/ws/delivery/                # Interface livreur
```

### Commandes de Gestion

```bash
# Créer des données de test
python manage.py create_test_data

# Nettoyer les données expirées
python manage.py cleanup_expired_data

# Calculer les statistiques
python manage.py calculate_stats

# Envoyer les notifications
python manage.py send_notifications
```

## 🧪 Tests

### Lancer les Tests

```bash
# Tests unitaires
python manage.py test

# Tests avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html

# Tests d'API
python manage.py test --tag=api

# Tests d'intégration
python manage.py test --tag=integration
```

### Données de Test

```bash
# Charger les fixtures
python manage.py loaddata fixtures/users.json
python manage.py loaddata fixtures/restaurants.json
python manage.py loaddata fixtures/orders.json

# Créer des données aléatoires
python manage.py create_test_data --restaurants=20 --orders=100
```

## 🔒 Sécurité

### Fonctionnalités Implémentées

- **Authentification JWT** : Tokens sécurisés
- **Permissions granulaires** : Contrôle d'accès par rôle
- **Validation des données** : Sanitization des entrées
- **Protection CSRF** : Tokens anti-CSRF
- **Chiffrement** : Données sensibles chiffrées
- **Rate limiting** : Protection contre le spam

### Configuration Production

```python
# settings/production.py
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 📊 Monitoring et Analytics

### Métriques Disponibles

- **Commandes** : Volume, revenus, temps moyen
- **Restaurants** : Performance, popularité
- **Livreurs** : Efficacité, évaluations
- **Utilisateurs** : Acquisition, rétention

### Dashboards

- **Admin** : Vue globale de la plateforme
- **Restaurant** : Analytics spécifiques
- **Livreur** : Performances et gains

## 🌍 Déploiement

### Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: .
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://...
    depends_on:
      - db
      - redis
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Variables d'Environnement Production

```env
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:pass@db:5432/gourmetguide
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🤝 Contribution

### Workflow de Développement

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Pousser la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

### Standards de Code

- **PEP 8** : Style Python
- **Black** : Formatage automatique
- **Flake8** : Linting
- **Coverage** : Tests > 80%

## 📞 Support

### Documentation

- **API** : `/api/docs/` (Swagger)
- **Admin** : `/admin/doc/`
- **Guide utilisateur** : `/help/`

### Contact

- **Email** : support@gourmetguide.com
- **Issues** : GitHub Issues
- **Discord** : [Serveur communauté]

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Django Community** : Framework exceptionnel
- **Bootstrap** : Interface utilisateur
- **Stripe** : Solution de paiement
- **Google Maps** : Services de géolocalisation

---

## 🚀 Démarrage Rapide

```bash
# Installation rapide avec Docker
git clone <repository>
cd gourmetguide
cp .env.example .env
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata fixtures/*.json

# Accéder à l'application
# http://localhost:8000
```

## 📈 Roadmap

- [ ] Application mobile native (React Native)
- [ ] IA pour recommandations personnalisées
- [ ] Intégration avec plus de services de paiement
- [ ] Support multi-pays
- [ ] API publique pour partenaires
- [ ] Programme d'affiliation

---

**Développé avec ❤️ pour la communauté africaine**
