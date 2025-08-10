#!/usr/bin/env python3
"""
Script temporaire pour remplacer les ImageField par des CharField
pour permettre la création des migrations sans Pillow.
"""

import os
import re

def replace_imagefields_in_file(filepath):
    """Remplace les ImageField par des CharField dans un fichier."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les ImageField
    pattern = r'(\s+)(\w+)\s*=\s*models\.ImageField\(\s*([^)]+)\)'
    
    def replacement(match):
        indent = match.group(1)
        field_name = match.group(2)
        params = match.group(3)
        
        # Extraire les paramètres utiles
        new_params = []
        for param in params.split(','):
            param = param.strip()
            if param.startswith('_'):  # verbose_name
                new_params.append(param)
            elif param.startswith('blank='):
                new_params.append(param)
            elif param.startswith('null='):
                new_params.append('blank=True')  # Remplacer null=True par blank=True
            elif param.startswith('help_text='):
                new_params.append(param)
        
        # Ajouter max_length
        new_params.append('max_length=255')
        
        return f"{indent}{field_name} = models.CharField({', '.join(new_params)})"
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Modifié: {filepath}")

# Liste des fichiers à modifier
files_to_modify = [
    'restaurants/models.py',
    'delivery/models.py',
    'payments/models.py',
    'reviews/models.py',
    'loyalty/models.py',
    'notifications/models.py',
    'core/models.py',
]

for file_path in files_to_modify:
    if os.path.exists(file_path):
        replace_imagefields_in_file(file_path)

print("Terminé !")