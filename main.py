"""
Point d'entrée principal de l'application Kripta.
Gestionnaire de mots de passe et crypteur de dossiers.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from src.ui.main_window import MainWindow
from src.ui.dialogs.security_init_dialog import SecurityInitDialog
from src.security.bootstrap import (
    initialize_security_profile,
    verify_master_password,
    load_security_profile,
    verify_user_certificate,
)
from src.security.profile_protobuf import is_security_profile_initialized
import secrets


def check_and_initialize_security(app: QApplication) -> bool:
    """
    Vérifie si le profil de sécurité est initialisé.
    Si non, lance l'interface d'initialisation.
    
    Returns:
        bool: True si l'initialisation est OK (existe ou vient d'être créée), False si annulée
    """
    # Vérifier si le profil existe déjà
    if is_security_profile_initialized():
        # Vérifier que le certificat utilisateur correspond
        if not verify_user_certificate():
            QMessageBox.warning(
                None,
                "Erreur de sécurité",
                "Le certificat utilisateur ne correspond pas. Réinitialisation nécessaire."
            )
            # TODO: Gérer la réinitialisation si l'utilisateur a changé
            return False
        
        # Le profil existe, on peut continuer
        return True
    
    # Pas encore initialisé : afficher le dialogue d'initialisation
    dialog = SecurityInitDialog()
    if dialog.exec() != dialog.DialogCode.Accepted:
        # Utilisateur a annulé
        return False
    
    values = dialog.get_values()
    
    # Vérifier que les mots de passe correspondent
    if values["password"] != values["password_confirm"]:
        QMessageBox.warning(
            None,
            "Erreur",
            "Les mots de passe ne correspondent pas."
        )
        return False
    
    if len(values["password"]) < 8:
        QMessageBox.warning(
            None,
            "Erreur",
            "Le mot de passe doit contenir au moins 8 caractères."
        )
        return False
    
    # Gérer la clé de récupération
    recovery_key = None
    if values["import_recovery_key"] and values["recovery_key_file"]:
        # Importer une clé de récupération existante
        from src.security.bootstrap import import_recovery_key_file
        recovery_key = import_recovery_key_file(values["recovery_key_file"])
        
        if not recovery_key:
            QMessageBox.warning(
                None,
                "Erreur",
                "Impossible d'importer la clé de récupération. Vérifiez que le fichier est valide."
            )
            return False
        
        QMessageBox.information(
            None,
            "Clé importée",
            "La clé de récupération a été importée avec succès."
        )
    
    elif values["generate_recovery_key"]:
        # Générer une nouvelle clé de récupération
        recovery_key = secrets.token_bytes(32)
        
        # Sauvegarder la clé dans un fichier que l'utilisateur pourra cacher
        from src.core.config import SECURITY_DIR
        recovery_file = SECURITY_DIR / "recovery_key.kripta"
        
        try:
            # Chiffrer et sauvegarder
            from src.security.bootstrap import encrypt_with_app_cert
            encrypted = encrypt_with_app_cert(recovery_key)
            with open(recovery_file, "wb") as f:
                f.write(encrypted)
            
            QMessageBox.information(
                None,
                "Clé de récupération générée",
                f"Une clé de récupération a été générée et sauvegardée dans :\n{recovery_file}\n\n"
                f"Conservez ce fichier en lieu sûr (clé USB, cloud, etc.).\n"
                f"Seule cette application pourra la lire."
            )
        except Exception as e:
            QMessageBox.warning(
                None,
                "Attention",
                f"Impossible de sauvegarder la clé de récupération : {e}\n"
                f"Vous pouvez l'importer plus tard."
            )
    
    # Initialiser le profil
    try:
        profile = initialize_security_profile(
            master_password=values["password"],
            recovery_key=recovery_key,
        )
        
        QMessageBox.information(
            None,
            "Initialisation réussie",
            "Votre profil de sécurité a été créé avec succès !"
        )
        
        return True
    except Exception as e:
        QMessageBox.critical(
            None,
            "Erreur",
            f"Erreur lors de l'initialisation : {e}"
        )
        return False


def main():
    """Fonction principale de l'application."""
    app = QApplication(sys.argv)
    
    # Vérifier et initialiser la sécurité si nécessaire
    if not check_and_initialize_security(app):
        # L'utilisateur a annulé ou une erreur s'est produite
        sys.exit(1)
    
    # Afficher le menu principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
