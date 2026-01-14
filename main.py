"""
Point d'entrée principal de l'application Kripta.
Gestionnaire de mots de passe et crypteur de dossiers.
"""

import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Fonction principale de l'application."""
    app = QApplication(sys.argv)
    
    # Afficher le menu principal par défaut
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
