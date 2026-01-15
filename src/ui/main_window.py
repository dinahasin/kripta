"""
Menu principal de l'application Kripta.
Affiche les trois options principales : Gestionnaire de mots de passe, Crypteur de fichiers, Spaces optimisations.
Inclut aussi un menu pour les actions globales (Aide, effacement des données de sécurité, etc.).
"""

from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QStackedWidget, QWidget, QVBoxLayout, QLineEdit
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
        self.disk_analyzer_view = None
        
        # Initialisation de l'interface
        self._setup_ui()
        self._setup_menu()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur et les connexions de signaux."""
        # Connexion des boutons aux signaux
        self.ui.btn_password_manager.clicked.connect(self._open_password_manager)
        self.ui.btn_file_encryptor.clicked.connect(self._show_coming_soon)
        self.ui.btn_disk_analyzer.clicked.connect(self._open_disk_analyzer)

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
        
        # Menu Données
        menu_data = self.menuBar().addMenu("Données")
        
        action_export = menu_data.addAction("📤 Exporter les mots de passe...")
        action_export.triggered.connect(self._export_passwords)
        
        action_import = menu_data.addAction("📥 Importer les mots de passe...")
        action_import.triggered.connect(self._import_passwords)
        
        menu_data.addSeparator()
        
        action_logout = menu_data.addAction("🚪 Se déconnecter")
        action_logout.triggered.connect(self._logout)
        
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
    
    def _open_disk_analyzer(self):
        """Ouvre l'analyseur de disque dans la fenêtre principale."""
        if self.disk_analyzer_view is None:
            from src.disk_analyzer.ui import DiskAnalyzerWidget
            
            self.disk_analyzer_view = DiskAnalyzerWidget(self)
            self.disk_analyzer_view.back_requested.connect(self._show_home)
            self.stacked_widget.addWidget(self.disk_analyzer_view)
        
        self.stacked_widget.setCurrentWidget(self.disk_analyzer_view)
        self.setWindowTitle("Kripta - Analyseur d'Espace Disque")
    
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

    def _export_passwords(self):
        """Exporte les mots de passe dans un fichier chiffré."""
        from PySide6.QtWidgets import QFileDialog, QInputDialog
        from src.password_manager.export_import import export_passwords_to_file
        from src.password_manager.service import PasswordManagerService
        
        # Demander le chemin du fichier
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les mots de passe",
            "mots_de_passe_kripta.kdb",
            "Kripta Database (*.kdb);;Tous les fichiers (*.*)"
        )
        
        if not file_path:
            return
        
        # Demander confirmation du mot de passe maître
        password, ok = QInputDialog.getText(
            self,
            "Confirmation",
            "Entrez votre mot de passe maître pour chiffrer l'export:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not password:
            return
        
        # Exporter
        service = PasswordManagerService(self.encrypted_db)
        if export_passwords_to_file(service, Path(file_path), password):
            QMessageBox.information(
                self,
                "Export réussi",
                f"✓ Vos mots de passe ont été exportés avec succès dans:\n{file_path}"
            )
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Une erreur est survenue lors de l'export."
            )
    
    def _import_passwords(self):
        """Importe les mots de passe depuis un fichier chiffré."""
        from PySide6.QtWidgets import QFileDialog, QInputDialog, QLineEdit
        from src.password_manager.export_import import import_passwords_from_file
        from src.password_manager.service import PasswordManagerService
        
        # Demander le fichier
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer les mots de passe",
            "",
            "Kripta Database (*.kdb);;Tous les fichiers (*.*)"
        )
        
        if not file_path:
            return
        
        # Demander le mot de passe
        password, ok = QInputDialog.getText(
            self,
            "Mot de passe",
            "Entrez le mot de passe maître utilisé pour chiffrer ce fichier:",
            QLineEdit.EchoMode.Password
        )
        
        if not ok or not password:
            return
        
        # Importer
        service = PasswordManagerService(self.encrypted_db)
        success, count = import_passwords_from_file(service, Path(file_path), password)
        
        if success:
            QMessageBox.information(
                self,
                "Import réussi",
                f"✓ {count} mot(s) de passe importé(s) avec succès !"
            )
            # Rafraîchir la vue si le gestionnaire est ouvert
            if self.password_manager_view:
                self.password_manager_view.refresh_list()
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'importer les données.\nVérifiez que le mot de passe est correct."
            )
    
    def _logout(self):
        """Déconnexion avec options de gestion des données."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout
        
        # Créer un dialogue personnalisé
        dialog = QDialog(self)
        dialog.setWindowTitle("Déconnexion")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titre
        lbl_title = QLabel("🚪 Déconnexion")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl_title)
        
        lbl_info = QLabel("Que souhaitez-vous faire avant de vous déconnecter ?")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(lbl_info)
        
        # Option: Supprimer les données
        chk_delete = QCheckBox("Supprimer tous les mots de passe enregistrés")
        chk_delete.setStyleSheet("font-size: 13px; padding: 5px;")
        layout.addWidget(chk_delete)
        
        # Avertissement
        lbl_warning = QLabel("⚠ Si vous cochez cette option, TOUTES vos données seront définitivement supprimées (profil de sécurité, certificats, mots de passe).")
        lbl_warning.setWordWrap(True)
        lbl_warning.setStyleSheet("color: #e74c3c; font-size: 11px; padding: 10px; background-color: #fadbd8; border-radius: 5px;")
        lbl_warning.setVisible(False)
        layout.addWidget(lbl_warning)
        
        # Afficher l'avertissement quand la case est cochée
        chk_delete.toggled.connect(lbl_warning.setVisible)
        
        layout.addSpacing(10)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setStyleSheet("""
            background-color: #ecf0f1; 
            color: #2c3e50; 
            font-weight: bold; 
            padding: 10px;
            border-radius: 5px;
        """)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_logout = QPushButton("Se déconnecter")
        btn_logout.setMinimumHeight(40)
        btn_logout.setStyleSheet("""
            background-color: #e74c3c; 
            color: white; 
            font-weight: bold; 
            padding: 10px;
            border-radius: 5px;
        """)
        btn_logout.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_logout)
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Fermer la connexion DB AVANT de supprimer les fichiers
            try:
                if hasattr(self, 'encrypted_db') and self.encrypted_db:
                    self.encrypted_db.connection.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture de la DB: {e}")
            
            # Supprimer les données si demandé
            if chk_delete.isChecked():
                try:
                    # Utiliser reset_security_state qui supprime TOUT
                    reset_security_state()
                    
                    QMessageBox.information(
                        self,
                        "Déconnexion",
                        "✓ Toutes vos données ont été supprimées.\n\n"
                        "Au prochain démarrage, vous devrez reconfigurer l'application."
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Attention",
                        f"Erreur lors de la suppression des données:\n{e}\n\n"
                        "Certaines données peuvent ne pas avoir été supprimées."
                    )
            else:
                QMessageBox.information(
                    self,
                    "Déconnexion",
                    "Vous avez été déconnecté.\n\n"
                    "Vos données sont conservées pour la prochaine connexion."
                )
            
            # Fermer l'application
            QApplication.instance().quit()
    
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
