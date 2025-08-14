#!/bin/bash

echo "🚀 Démarrage du projet Django VIVO"
echo "=================================="

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances si nécessaire
if [ ! -f "venv/lib/python*/site-packages/django" ]; then
    echo "📥 Installation des dépendances..."
    pip install -r requirements.txt
fi

# Vérifier si la base de données existe
if [ ! -f "db.sqlite3" ]; then
    echo "🗄️  Configuration de la base de données..."
    python manage.py makemigrations
    python manage.py migrate
    
    echo "👤 Création du super utilisateur..."
    echo "admin" | python manage.py createsuperuser --email admin@vivo.com --username admin --noinput
    echo "✅ Super utilisateur créé: admin@vivo.com / admin"
fi

# Lancer le serveur
echo "🌐 Lancement du serveur Django..."
echo "📍 Interface d'administration: http://localhost:8000/admin/"
echo "🔑 Identifiants: admin@vivo.com / admin"
echo "🌍 API REST: http://localhost:8000/api/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python manage.py runserver 0.0.0.0:8000