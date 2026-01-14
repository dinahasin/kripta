from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from src.security.bootstrap import verify_master_password, load_security_profile
from src.storage.database import DB_SALT_KEY, get_or_create_db_salt, derive_database_key

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kripta - Connexion Sécurisée")
        self.setModal(True)
        self.setMinimumSize(450, 350)
        self.derived_key = None
        self.setup_ui()
        self.apply_modern_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header avec icône de sécurité
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)
        
        # Titre principal
        lbl_title = QLabel("🔐 Kripta")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        lbl_title.setFont(title_font)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(lbl_title)
        
        # Sous-titre
        lbl_subtitle = QLabel("Gestionnaire de Mots de Passe Sécurisé")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        lbl_subtitle.setFont(subtitle_font)
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_subtitle.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(lbl_subtitle)
        
        layout.addLayout(header_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ecf0f1; max-height: 2px;")
        layout.addWidget(separator)
        
        layout.addSpacing(10)

        # Label d'instruction
        lbl_info = QLabel("Mot de passe maître")
        info_font = QFont()
        info_font.setPointSize(10)
        info_font.setBold(True)
        lbl_info.setFont(info_font)
        lbl_info.setStyleSheet("color: #2c3e50;")
        layout.addWidget(lbl_info)

        # Champ de mot de passe
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Entrez votre mot de passe...")
        self.txt_password.setMinimumHeight(45)
        layout.addWidget(self.txt_password)
        
        layout.addSpacing(10)

        # Boutons
        hbox_btns = QHBoxLayout()
        hbox_btns.setSpacing(15)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setMinimumHeight(45)
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_ok = QPushButton("🔓 Déverrouiller")
        btn_ok.setMinimumHeight(45)
        btn_ok.clicked.connect(self.check_password)
        btn_ok.setDefault(True)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)

        hbox_btns.addWidget(btn_cancel)
        hbox_btns.addWidget(btn_ok)
        layout.addLayout(hbox_btns)
        
        # Spacer pour pousser le contenu vers le haut
        layout.addStretch()

    def apply_modern_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 13px;
                background-color: #f8f9fa;
            }
            
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #ffffff;
            }
            
            QPushButton {
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            
            QPushButton[text="🔓 Déverrouiller"] {
                background-color: #3498db;
                color: white;
            }
            
            QPushButton[text="🔓 Déverrouiller"]:hover {
                background-color: #2980b9;
            }
            
            QPushButton[text="🔓 Déverrouiller"]:pressed {
                background-color: #21618c;
            }
            
            QPushButton[text="Annuler"] {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            
            QPushButton[text="Annuler"]:hover {
                background-color: #d5dbdb;
            }
        """)

    def check_password(self):
        password = self.txt_password.text()
        if not password:
            return

        profile = load_security_profile()
        if not profile:
             QMessageBox.critical(self, "Erreur", "Profil de sécurité introuvable !")
             self.reject()
             return

        if verify_master_password(profile, password):
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
            self.txt_password.clear()
            self.txt_password.setFocus()

    def get_password(self):
        return self.txt_password.text()
