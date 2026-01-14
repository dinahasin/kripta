"""
Menu principal de l'application Kripta.
Affiche les trois options principales : Gestionnaire de mots de passe, Crypteur de fichiers, Spaces optimisations.
Inclut aussi un menu pour les actions globales (Aide, effacement des données de sécurité, etc.).
"""

from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication
from PySide6.QtCore import Signal
from .main_window_ui import Ui_MenuPrincipal
from src.security.bootstrap import reset_security_state


class MainWindow(QMainWindow):
    """Fenêtre principale (menu) de l'application Kripta."""
    
    # Signaux pour la navigation
    password_manager_requested = Signal()
    file_encryptor_requested = Signal()
    disk_analyzer_requested = Signal()
    
    def __init__(self, encrypted_db, parent=None):
        super().__init__(parent)
        self.encrypted_db = encrypted_db
        self.ui = Ui_MenuPrincipal()
        self.ui.setupUi(self)
        self.pm_window = None # Keep reference to avoid GC
        
        # Initialisation de l'interface
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur et les connexions de signaux."""
        # Connexion des boutons aux signaux
        self.ui.btn_password_manager.clicked.connect(self._open_password_manager)
        self.ui.btn_file_encryptor.clicked.connect(self.file_encryptor_requested.emit)
        self.ui.btn_disk_analyzer.clicked.connect(self.disk_analyzer_requested.emit)

    def _open_password_manager(self):
        from src.password_manager.service import PasswordManagerService
        from src.ui.password_manager.window import PasswordManagerWindow
        
        service = PasswordManagerService(self.encrypted_db)
        self.pm_window = PasswordManagerWindow(service, self)
        self.pm_window.show()

        # Menu Sécurité : effacer les données personnelles
        if hasattr(self.ui, "action_clear_security"):
            self.ui.action_clear_security.triggered.connect(self._on_clear_security_triggered)

    def _on_clear_security_triggered(self):
        """
        Efface toutes les données de sécurité locales après confirmation de l'utilisateur.
        """
        reply = QMessageBox.question(
            self,
            "Effacer mes données de sécurité",
            (
                "Voulez-vous vraiment effacer toutes vos données de sécurité locales ?\n\n"
                "- Profil de sécurité (mot de passe maître, métadonnées)\n"
                "- Certificats applicatif et utilisateur\n"
                "- Clés de récupération enregistrées\n"
                "- Données de mots de passe chiffrés\n\n"
                "Cette opération est irréversible. L'application devra être réinitialisée au prochain démarrage."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            reset_security_state()
            QMessageBox.information(
                self,
                "Données effacées",
                "Vos données de sécurité locales ont été supprimées.\n"
                "L'application va se fermer, vous pourrez la reconfigurer au prochain lancement.",
            )
            QApplication.instance().quit()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue lors de la suppression des données :\n{e}",
            )
