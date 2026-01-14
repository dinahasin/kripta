"""
Menu principal de l'application Kripta.
Affiche les trois options principales : Gestionnaire de mots de passe, Crypteur de fichiers, Spaces optimisations.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Signal
from .main_window_ui import Ui_MenuPrincipal


class MainWindow(QMainWindow):
    """Fenêtre principale (menu) de l'application Kripta."""
    
    # Signaux pour la navigation
    password_manager_requested = Signal()
    file_encryptor_requested = Signal()
    disk_analyzer_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MenuPrincipal()
        self.ui.setupUi(self)
        
        # Initialisation de l'interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur et les connexions de signaux."""
        # Connexion des boutons aux signaux
        self.ui.btn_password_manager.clicked.connect(self.password_manager_requested.emit)
        self.ui.btn_file_encryptor.clicked.connect(self.file_encryptor_requested.emit)
        self.ui.btn_disk_analyzer.clicked.connect(self.disk_analyzer_requested.emit)
