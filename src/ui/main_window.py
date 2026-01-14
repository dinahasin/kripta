"""
Menu principal de l'application Kripta.
Affiche les trois options principales : Gestionnaire de mots de passe, Crypteur de fichiers, Spaces optimisations.
Inclut aussi un menu pour les actions globales (Aide, effacement des données de sécurité, etc.).
"""

from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QStackedWidget, QWidget, QVBoxLayout
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
        
        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create home widget - we'll manually add the UI elements
        self.home_widget = QWidget()
        self.ui = Ui_MenuPrincipal()
        
        # Setup UI elements on a temporary main window to extract the central widget
        temp_window = QMainWindow()
        self.ui.setupUi(temp_window)
        
        # Extract the central widget content and reparent it to our home_widget
        content = temp_window.centralWidget()
        layout = QVBoxLayout(self.home_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        if content:
            content.setParent(self.home_widget)
            layout.addWidget(content)
        
        self.stacked_widget.addWidget(self.home_widget)
        
        # Référence pour les vues
        self.password_manager_view = None
        
        # Initialisation de l'interface
        self._setup_ui()
        self._setup_menu()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur et les connexions de signaux."""
        # Connexion des boutons aux signaux
        self.ui.btn_password_manager.clicked.connect(self._open_password_manager)
        self.ui.btn_file_encryptor.clicked.connect(self._show_coming_soon)
        self.ui.btn_disk_analyzer.clicked.connect(self._show_coming_soon)

    def _setup_menu(self):
        """Configure le menu avec les raccourcis vers les fonctionnalités."""
        # Menu Fonctionnalités
        menu_features = self.menuBar().addMenu("Fonctionnalités")
        
        action_passwords = menu_features.addAction("🔑 Gestionnaire de mots de passe")
        action_passwords.triggered.connect(self._open_password_manager)
        
        action_files = menu_features.addAction("🔒 Crypteur de fichiers")
        action_files.triggered.connect(self._show_coming_soon)
        
        action_disk = menu_features.addAction("💾 Optimisation d'espace")
        action_disk.triggered.connect(self._show_coming_soon)
        
        # Menu Aide
        menu_help = self.menuBar().addMenu("Aide")
        
        if hasattr(self.ui, "action_about"):
            menu_help.addAction(self.ui.action_about)
        
        if hasattr(self.ui, "action_clear_security"):
            self.ui.action_clear_security.triggered.connect(self._on_clear_security_triggered)
            menu_help.addAction(self.ui.action_clear_security)

    def _open_password_manager(self):
        """Ouvre le gestionnaire de mots de passe dans la fenêtre principale."""
        if self.password_manager_view is None:
            from src.password_manager.service import PasswordManagerService
            from src.ui.password_manager.password_manager_widget import PasswordManagerWidget
            
            service = PasswordManagerService(self.encrypted_db)
            self.password_manager_view = PasswordManagerWidget(service, self)
            self.password_manager_view.back_requested.connect(self._show_home)
            self.stacked_widget.addWidget(self.password_manager_view)
        
        self.stacked_widget.setCurrentWidget(self.password_manager_view)
        self.setWindowTitle("Kripta - Gestionnaire de Mots de Passe")
    
    def _show_home(self):
        """Retourne à la page d'accueil."""
        self.stacked_widget.setCurrentWidget(self.home_widget)
        self.setWindowTitle("Kripta - Menu Principal")
    
    def _show_coming_soon(self):
        """Affiche un message pour les fonctionnalités à venir."""
        QMessageBox.information(
            self,
            "Bientôt disponible",
            "Cette fonctionnalité sera disponible dans une prochaine version."
        )

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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
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
