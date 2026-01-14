"""
Utilitaires pour l'export et l'import des données de mots de passe.
"""

import json
import base64
from pathlib import Path
from typing import List, Optional
from src.password_manager.models import PasswordEntry
from src.password_manager.service import PasswordManagerService
from src.crypto.encryption import encrypt_aes_gcm, decrypt_aes_gcm
from src.crypto.keys import derive_key_from_password
import secrets


def export_passwords_to_file(service: PasswordManagerService, export_path: Path, master_password: str) -> bool:
    """
    Exporte tous les mots de passe dans un fichier chiffré.
    
    Args:
        service: Service de gestion des mots de passe
        export_path: Chemin du fichier d'export
        master_password: Mot de passe maître pour chiffrer l'export
    
    Returns:
        True si l'export a réussi, False sinon
    """
    try:
        # Récupérer tous les mots de passe
        entries = service.list_entries()
        
        # Convertir en dictionnaire
        data = {
            "version": "1.0",
            "entries": [
                {
                    "id": entry.id,
                    "title": entry.title,
                    "username": entry.username,
                    "password": entry.password,
                    "url": entry.url,
                    "notes": entry.notes,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                }
                for entry in entries
            ]
        }
        
        # Sérialiser en JSON
        json_data = json.dumps(data, indent=2).encode('utf-8')
        
        # Générer un sel pour la dérivation de clé
        salt = secrets.token_bytes(16)
        
        # Dériver une clé depuis le mot de passe maître
        key = derive_key_from_password(master_password, salt, length=32)
        
        # Chiffrer les données
        encrypted_data = encrypt_aes_gcm(key, json_data)
        
        # Écrire dans le fichier (sel + données chiffrées)
        with open(export_path, 'wb') as f:
            f.write(salt)
            f.write(encrypted_data)
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'export: {e}")
        return False


def import_passwords_from_file(service: PasswordManagerService, import_path: Path, master_password: str) -> tuple[bool, int]:
    """
    Importe les mots de passe depuis un fichier chiffré.
    
    Args:
        service: Service de gestion des mots de passe
        import_path: Chemin du fichier d'import
        master_password: Mot de passe maître pour déchiffrer l'import
    
    Returns:
        Tuple (succès, nombre d'entrées importées)
    """
    try:
        # Lire le fichier
        with open(import_path, 'rb') as f:
            salt = f.read(16)
            encrypted_data = f.read()
        
        # Dériver la clé depuis le mot de passe maître
        key = derive_key_from_password(master_password, salt, length=32)
        
        # Déchiffrer les données
        try:
            json_data = decrypt_aes_gcm(key, encrypted_data)
        except Exception:
            # Mot de passe incorrect
            return False, 0
        
        # Désérialiser le JSON
        data = json.loads(json_data.decode('utf-8'))
        
        # Vérifier la version
        if data.get("version") != "1.0":
            return False, 0
        
        # Importer les entrées
        count = 0
        for entry_data in data.get("entries", []):
            try:
                # Créer une nouvelle entrée (avec un nouvel ID pour éviter les conflits)
                service.add_entry(
                    title=entry_data["title"],
                    username=entry_data["username"],
                    password=entry_data["password"],
                    url=entry_data.get("url", ""),
                    notes=entry_data.get("notes", "")
                )
                count += 1
            except Exception as e:
                print(f"Erreur lors de l'import de l'entrée {entry_data.get('title')}: {e}")
                continue
        
        return True, count
    except Exception as e:
        print(f"Erreur lors de l'import: {e}")
        return False, 0
