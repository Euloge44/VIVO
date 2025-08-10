#!/usr/bin/env python3
"""
Script pour corriger les modèles Django en remplaçant les ImageField.
"""

import os
import re

def fix_imagefields_in_file(filepath):
    """Corrige les ImageField dans un fichier."""
    if not os.path.exists(filepath):
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remplacer les ImageField avec leurs paramètres
    patterns = [
        # Pattern général pour ImageField
        (r'models\.ImageField\([^)]+\)', lambda m: convert_imagefield(m.group(0))),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Corrigé: {filepath}")

def convert_imagefield(imagefield_str):
    """Convertit un ImageField en CharField."""
    # Extraire le verbose_name
    verbose_name_match = re.search(r"_\('([^']+)'\)", imagefield_str)
    verbose_name = verbose_name_match.group(0) if verbose_name_match else "_('Image')"
    
    # Vérifier si blank=True est présent
    blank = ', blank=True' if 'blank=True' in imagefield_str else ''
    
    # Vérifier si help_text est présent
    help_text_match = re.search(r"help_text=_\('([^']+)'\)", imagefield_str)
    help_text = f", help_text=_('URL de l\\'image')" if not help_text_match else f", {help_text_match.group(0)}"
    
    return f"models.CharField({verbose_name}, max_length=255{blank}{help_text})"

# Fichiers à corriger
files_to_fix = [
    'restaurants/models.py',
    'delivery/models.py', 
    'payments/models.py',
    'reviews/models.py',
    'loyalty/models.py',
    'notifications/models.py',
    'core/models.py',
]

for file_path in files_to_fix:
    fix_imagefields_in_file(file_path)

print("Correction terminée !")