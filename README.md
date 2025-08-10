# GourmetGuide 🍴

Une plateforme complète de découverte culinaire et de livraison de repas au Togo, développée avec Django.

## 🌟 Fonctionnalités

### Pour les Clients
- 🔍 **Recherche avancée** de restaurants par localisation, cuisine, prix
- 🛒 **Commande en ligne** avec panier intelligent
- 📱 **Paiements mobiles** (Tmoney, Flooz) et cartes bancaires
- 🚚 **Suivi en temps réel** des livraisons
- ⭐ **Système d'avis** et de notation
- 🎁 **Programme de fidélité** avec points et récompenses
- 🔔 **Notifications temps réel** (WebSocket)

### Pour les Restaurants
- 📊 **Tableau de bord** avec statistiques détaillées
- 🍽️ **Gestion du menu** et des prix
- 📋 **Gestion des commandes** en temps réel
- 📈 **Analytics** et rapports de vente
- 👥 **Gestion du personnel** et des rôles
- 🎯 **Promotions** et offres spéciales

### Pour les Livreurs
- 🗺️ **Interface de livraison** avec géolocalisation
- 📦 **Gestion des livraisons** assignées
- 💰 **Suivi des revenus** et statistiques
- 🚴 **Optimisation des trajets**

### Pour les Administrateurs
- 🛡️ **Gestion complète** de la plateforme
- 📊 **Analytics globales** et KPIs
- 👤 **Gestion des utilisateurs** et modération
- 💳 **Gestion des paiements** et transactions
- 🔧 **Configuration** du système

## 🛠️ Technologies Utilisées

### Backend
- **Django 5.0** - Framework web principal
- **Django REST Framework** - APIs REST
- **PostgreSQL** - Base de données (SQLite en développement)
- **Redis** - Cache et messages (Django Channels)
- **Celery** - Tâches asynchrones

### Frontend
- **Django Templates** - Rendu côté serveur
- **Bootstrap 5** - Framework CSS
- **JavaScript ES6+** - Interactivité
- **WebSockets** - Notifications temps réel

### Intégrations
- **Google Maps API** - Géolocalisation
- **Stripe** - Paiements internationaux
- **Tmoney/Flooz** - Paiements mobiles locaux (simulation)
- **Django Channels** - WebSockets
- **Django Allauth** - Authentification sociale

### Déploiement
- **Docker** & **Docker Compose**
- **Nginx** - Serveur web
- **Gunicorn** - Serveur WSGI
- **PostgreSQL** - Base de données production

## 📁 Structure du Projet

```
gourmetguide/
├── accounts/           # Gestion des utilisateurs multi-rôles
├── restaurants/        # Gestion des restaurants et menus
├── orders/            # Système de commandes et panier
├── delivery/          # Gestion des livraisons
├── payments/          # Système de paiement
├── reviews/           # Avis et notations
├── loyalty/           # Programme de fidélité
├── notifications/     # Notifications temps réel
├── analytics/         # Statistiques et rapports
├── core/             # Utilitaires et pages communes
├── templates/        # Templates Django
├── static/           # Fichiers statiques (CSS, JS, images)
├── media/            # Fichiers uploadés
├── locale/           # Traductions (FR/EN)
└── gourmetguide/     # Configuration principale
```

## 🚀 Installation et Configuration

### Prérequis
- Python 3.11+
- Node.js 18+ (pour les assets frontend)
- PostgreSQL 14+ (pour la production)
- Redis 6+ (pour les WebSockets et cache)

### Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd gourmetguide
```

2. **Créer un environnement virtuel**
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

4. **Configuration de l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

5. **Base de données**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Créer des données de test**
```bash
python manage.py create_test_data
```

8. **Collecter les fichiers statiques**
```bash
python manage.py collectstatic
```

9. **Démarrer le serveur**
```bash
python manage.py runserver
```

### Variables d'Environnement

Créez un fichier `.env` basé sur `.env.example` :

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_URL=sqlite:///db.sqlite3
# ou pour PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/gourmetguide

# Redis (pour Django Channels et cache)
REDIS_URL=redis://localhost:6379/0

# APIs externes
GOOGLE_MAPS_API_KEY=your-google-maps-key
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Cloudinary (optionnel)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 🐳 Déploiement avec Docker

1. **Construire et démarrer les conteneurs**
```bash
docker-compose up --build
```

2. **Exécuter les migrations**
```bash
docker-compose exec web python manage.py migrate
```

3. **Créer un superutilisateur**
```bash
docker-compose exec web python manage.py createsuperuser
```

4. **Créer des données de test**
```bash
docker-compose exec web python manage.py create_test_data
```

## 📱 API REST

L'application expose une API REST complète :

### Authentification
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/logout/` - Déconnexion
- `GET /api/auth/profile/` - Profil utilisateur

### Restaurants
- `GET /api/restaurants/` - Liste des restaurants
- `GET /api/restaurants/{id}/` - Détails d'un restaurant
- `GET /api/restaurants/{id}/menu/` - Menu d'un restaurant
- `POST /api/restaurants/search/` - Recherche avancée

### Commandes
- `GET /api/orders/` - Liste des commandes
- `POST /api/orders/` - Créer une commande
- `GET /api/orders/{id}/` - Détails d'une commande
- `POST /api/orders/{id}/cancel/` - Annuler une commande

### Panier
- `GET /api/orders/cart/` - Contenu du panier
- `POST /api/orders/cart/add/` - Ajouter un article
- `PUT /api/orders/cart/update/` - Modifier un article
- `DELETE /api/orders/cart/remove/` - Supprimer un article

Documentation complète disponible à `/api/` (DRF Browsable API).

## 🌍 Internationalisation

L'application supporte le français et l'anglais :

```bash
# Générer les fichiers de traduction
python manage.py makemessages -l en
python manage.py makemessages -l fr

# Compiler les traductions
python manage.py compilemessages
```

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Tests avec coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📊 Données de Test

Le projet inclut des données de test réalistes :

- **5 restaurants** avec menus complets
- **15 utilisateurs** (clients, restaurateurs, livreurs)
- **Coordonnées GPS** réelles de Lomé, Togo
- **Catégories** de cuisine locales et internationales

```bash
# Créer des données de test
python manage.py create_test_data

# Supprimer et recréer les données
python manage.py create_test_data --clear
```

## 🔐 Comptes de Test

Après avoir exécuté `create_test_data` :

### Clients
- `client1@test.com` / `testpass123`
- `client2@test.com` / `testpass123`

### Restaurants
- `baobab@restaurant.com` / `testpass123`
- `mama@restaurant.com` / `testpass123`
- `pizza@restaurant.com` / `testpass123`

### Livreurs
- `livreur1@test.com` / `testpass123`
- `livreur2@test.com` / `testpass123`

### Admin
- `admin@gourmetguide.com` / `admin123`

## 🎨 Personnalisation

### Thème et Couleurs
Les couleurs principales sont définies dans `static/css/main.css` :

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
}
```

### Templates
Les templates utilisent Bootstrap 5 et sont entièrement personnalisables dans le dossier `templates/`.

## 🔧 Commandes de Gestion

```bash
# Créer une nouvelle application Django
python manage.py startapp nom_app

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic

# Démarrer le serveur de développement
python manage.py runserver

# Shell Django
python manage.py shell

# Créer des données de test
python manage.py create_test_data [--clear]
```

## 📈 Fonctionnalités Avancées

### Géolocalisation
- Calcul automatique des distances
- Zones de livraison personnalisées
- Optimisation des trajets pour les livreurs

### Paiements
- Intégration Stripe pour les cartes bancaires
- Simulation des paiements mobiles (Tmoney, Flooz)
- Gestion des portefeuilles électroniques
- Paiements en espèces à la livraison

### Notifications Temps Réel
- WebSockets avec Django Channels
- Notifications push (Firebase)
- Emails transactionnels
- SMS (intégration à prévoir)

### Programme de Fidélité
- Points gagnés à chaque commande
- Niveaux de fidélité (Bronze, Argent, Or, Platine)
- Récompenses et réductions exclusives
- Parrainage avec bonus

## 🤝 Contribution

1. Fork le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -am 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

- **Email** : support@gourmetguide.com
- **Documentation** : [docs.gourmetguide.com](https://docs.gourmetguide.com)
- **Issues** : [GitHub Issues](https://github.com/votre-org/gourmetguide/issues)

## 🗺️ Roadmap

### Phase 1 (Actuelle) ✅
- [x] Architecture de base Django
- [x] Authentification multi-rôles
- [x] Gestion des restaurants et menus
- [x] Système de commandes
- [x] Interface utilisateur responsive
- [x] API REST complète

### Phase 2 (En cours) 🚧
- [ ] Intégration Google Maps
- [ ] Paiements Stripe
- [ ] Notifications temps réel
- [ ] Programme de fidélité avancé

### Phase 3 (À venir) 📋
- [ ] Application mobile (React Native)
- [ ] Intelligence artificielle (recommandations)
- [ ] Expansion géographique
- [ ] Intégrations tiers avancées

---

**Développé avec ❤️ pour la communauté togolaise**
