# VIVO - Projet Django E-commerce

## 🚀 Description

VIVO est une application e-commerce complète construite avec Django et Django REST Framework. Elle offre une interface d'administration robuste et une API REST complète pour la gestion des utilisateurs, produits, catégories et commandes.

## ✨ Fonctionnalités

### 🔐 Authentification et Utilisateurs
- Modèle utilisateur personnalisé avec email comme identifiant principal
- Système d'authentification complet (inscription, connexion, déconnexion)
- Gestion des permissions et rôles utilisateur
- Interface d'administration Django intégrée

### 🛍️ Gestion des Produits
- Système de catégories hiérarchique
- Gestion complète des produits (nom, description, prix, stock, images)
- Filtrage et recherche par catégorie
- Gestion des stocks en temps réel

### 📦 Gestion des Commandes
- Système de commandes avec statuts multiples
- Suivi des commandes (En attente, En cours, Expédiée, Livrée, Annulée)
- Gestion des éléments de commande
- Calcul automatique des montants

### 🌐 API REST
- API complète avec Django REST Framework
- Authentification et permissions configurées
- Endpoints pour tous les modèles
- Pagination et filtrage intégrés

### 🎨 Interface d'Administration
- Dashboard admin Django personnalisé
- Gestion intuitive de tous les modèles
- Interface en français
- Filtres et recherche avancés

## 🛠️ Technologies Utilisées

- **Backend**: Django 5.2.5
- **API**: Django REST Framework 3.16.1
- **Base de données**: SQLite (développement)
- **Authentification**: Django Auth System
- **Images**: Pillow 11.3.0
- **CORS**: django-cors-headers 4.7.0

## 📋 Prérequis

- Python 3.13+
- pip
- virtualenv (recommandé)

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd vivo
```

### 2. Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un super utilisateur
```bash
python manage.py createsuperuser
```

### 6. Lancer le serveur
```bash
python manage.py runserver
```

## 🔑 Accès

- **Application principale**: http://localhost:8000/
- **Interface d'administration**: http://localhost:8000/admin/
- **API REST**: http://localhost:8000/api/

### Identifiants par défaut
- **Email**: admin@vivo.com
- **Nom d'utilisateur**: admin
- **Mot de passe**: admin

## 📚 Structure du Projet

```
vivo/
├── core/                   # Application principale
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues API
│   ├── serializers.py     # Sérialiseurs DRF
│   ├── admin.py           # Interface d'administration
│   └── urls.py            # URLs de l'application
├── vivo/                   # Configuration du projet
│   ├── settings.py        # Paramètres Django
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuration WSGI
├── manage.py              # Script de gestion Django
├── requirements.txt        # Dépendances Python
└── README.md              # Documentation
```

## 🗄️ Modèles de Données

### User (Utilisateur)
- Email (identifiant unique)
- Nom d'utilisateur, prénom, nom
- Téléphone, adresse
- Photo de profil
- Statut actif/inactif

### Category (Catégorie)
- Nom et description
- Timestamps de création/modification

### Product (Produit)
- Nom, description, prix
- Catégorie associée
- Image, stock disponible
- Statut actif/inactif

### Order (Commande)
- Utilisateur associé
- Statut de la commande
- Montant total
- Timestamps

### OrderItem (Élément de commande)
- Commande et produit associés
- Quantité et prix unitaire

## 🌐 API Endpoints

### Authentification
- `POST /api/users/register/` - Inscription utilisateur
- `POST /api/users/login/` - Connexion utilisateur
- `POST /api/users/logout/` - Déconnexion utilisateur

### Utilisateurs
- `GET /api/users/` - Liste des utilisateurs
- `POST /api/users/` - Créer un utilisateur
- `GET /api/users/{id}/` - Détails d'un utilisateur
- `PUT /api/users/{id}/` - Modifier un utilisateur
- `DELETE /api/users/{id}/` - Supprimer un utilisateur

### Catégories
- `GET /api/categories/` - Liste des catégories
- `POST /api/categories/` - Créer une catégorie
- `GET /api/categories/{id}/` - Détails d'une catégorie
- `GET /api/categories/{id}/products/` - Produits d'une catégorie

### Produits
- `GET /api/products/` - Liste des produits
- `POST /api/products/` - Créer un produit
- `GET /api/products/{id}/` - Détails d'un produit
- `POST /api/products/{id}/add_to_cart/` - Ajouter au panier

### Commandes
- `GET /api/orders/` - Liste des commandes
- `POST /api/orders/` - Créer une commande
- `GET /api/orders/{id}/` - Détails d'une commande
- `POST /api/orders/{id}/update_status/` - Mettre à jour le statut

## 🔧 Configuration

### Variables d'environnement
- `DEBUG`: Mode développement (True/False)
- `SECRET_KEY`: Clé secrète Django
- `ALLOWED_HOSTS`: Hôtes autorisés
- `DATABASE_URL`: URL de la base de données

### Base de données
Par défaut, le projet utilise SQLite pour le développement. Pour la production, configurez une base de données PostgreSQL ou MySQL dans `settings.py`.

## 🧪 Tests

Exécuter les tests du projet :
```bash
python test_project.py
```

Ou utiliser les tests Django standard :
```bash
python manage.py test
```

## 🚀 Déploiement

### Production
1. Modifier `DEBUG = False` dans `settings.py`
2. Configurer une base de données de production
3. Configurer les variables d'environnement
4. Collecter les fichiers statiques : `python manage.py collectstatic`
5. Utiliser Gunicorn ou uWSGI avec Nginx

### Docker (optionnel)
```bash
docker build -t vivo .
docker run -p 8000:8000 vivo
```

## 📝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contacter l'équipe de développement

## 🔄 Mises à jour

### Version actuelle : 1.0.0
- ✅ Modèles de base (User, Category, Product, Order, OrderItem)
- ✅ Interface d'administration complète
- ✅ API REST fonctionnelle
- ✅ Authentification et permissions
- ✅ Tests automatisés

### Prochaines fonctionnalités
- 🚧 Système de panier
- 🚧 Paiements en ligne
- 🚧 Notifications email
- 🚧 Interface utilisateur frontend
- 🚧 Système de commentaires et avis

---

**VIVO** - Votre plateforme e-commerce de confiance 🚀