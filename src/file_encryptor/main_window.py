"""
Fenêtre principale de l'application Kripta.
Utilise l'interface générée depuis main_window.ui
"""

from PySide6.QtWidgets import QMainWindow
from .main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Kripta."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialisation de l'interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Les connexions de signaux et l'initialisation de l'interface
        # seront ajoutées ici
        pass
