"""
Dialogues d'initialisation de la sécurité (PySide6).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QCheckBox, QFileDialog, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path


class SecurityInitDialog(QDialog):
    """
    Dialogue pour l'initialisation de la sécurité :
    - Saisie du mot de passe maître
    - Option de génération de clé de récupération
    - Option d'import de clé de récupération depuis un fichier
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kripta - Initialisation Sécurisée")
        self.setModal(True)
        self.setMinimumSize(550, 550)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        
        lbl_title = QLabel("🔐 Bienvenue sur Kripta")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        lbl_title.setFont(title_font)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(lbl_title)
        
        self.label_info = QLabel(
            "Configurez votre mot de passe maître et, optionnellement, une clé de récupération."
        )
        self.label_info.setWordWrap(True)
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        header_layout.addWidget(self.label_info)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ecf0f1; max-height: 2px;")
        layout.addWidget(separator)
        
        layout.addSpacing(10)

        # Password Section
        lbl_pwd_section = QLabel("Mot de passe maître")
        pwd_font = QFont()
        pwd_font.setPointSize(11)
        pwd_font.setBold(True)
        lbl_pwd_section.setFont(pwd_font)
        lbl_pwd_section.setStyleSheet("color: #2c3e50;")
        layout.addWidget(lbl_pwd_section)

        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_password.setPlaceholderText("Entrez votre mot de passe...")
        self.edit_password.setMinimumHeight(45)
        layout.addWidget(self.edit_password)

        self.edit_password_confirm = QLineEdit()
        self.edit_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_password_confirm.setPlaceholderText("Confirmez votre mot de passe...")
        self.edit_password_confirm.setMinimumHeight(45)
        layout.addWidget(self.edit_password_confirm)
        
        layout.addSpacing(10)

        # Recovery Key Section
        lbl_recovery_section = QLabel("Clé de récupération")
        lbl_recovery_section.setFont(pwd_font)
        lbl_recovery_section.setStyleSheet("color: #2c3e50;")
        layout.addWidget(lbl_recovery_section)

        self.checkbox_recovery = QCheckBox("Générer une clé de récupération (recommandé)")
        self.checkbox_recovery.setChecked(True)
        self.checkbox_recovery.toggled.connect(self._on_recovery_option_changed)
        self.checkbox_recovery.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(self.checkbox_recovery)

        # Import recovery key
        recovery_layout = QHBoxLayout()
        recovery_layout.setSpacing(10)
        
        self.checkbox_import_recovery = QCheckBox("Importer une clé existante")
        self.checkbox_import_recovery.toggled.connect(self._on_import_option_changed)
        self.checkbox_import_recovery.setStyleSheet("font-size: 12px;")
        recovery_layout.addWidget(self.checkbox_import_recovery)
        
        self.btn_browse_recovery = QPushButton("📁 Parcourir...")
        self.btn_browse_recovery.setEnabled(False)
        self.btn_browse_recovery.clicked.connect(self._browse_recovery_key)
        self.btn_browse_recovery.setMinimumHeight(35)
        self.btn_browse_recovery.setCursor(Qt.CursorShape.PointingHandCursor)
        recovery_layout.addWidget(self.btn_browse_recovery)
        
        layout.addLayout(recovery_layout)

        self.label_recovery_file = QLabel("")
        self.label_recovery_file.setStyleSheet("color: #27ae60; font-style: italic; font-size: 11px; padding-left: 5px;")
        layout.addWidget(self.label_recovery_file)

        self.recovery_file_path = None

        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)
        
        layout.addSpacing(10)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setMinimumHeight(45)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_ok = QPushButton("✓ Continuer")
        self.btn_ok.setMinimumHeight(45)
        self.btn_ok.clicked.connect(self._validate_and_accept)
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_ok)
        layout.addLayout(button_layout)
        
        self.apply_modern_style()

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
            
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #bdc3c7;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #3498db;
            }
            
            QPushButton {
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            
            QPushButton[text="✓ Continuer"] {
                background-color: #27ae60;
                color: white;
            }
            
            QPushButton[text="✓ Continuer"]:hover {
                background-color: #229954;
            }
            
            QPushButton[text="✓ Continuer"]:pressed {
                background-color: #1e8449;
            }
            
            QPushButton[text="Annuler"] {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            
            QPushButton[text="Annuler"]:hover {
                background-color: #d5dbdb;
            }
            
            QPushButton[text="📁 Parcourir..."] {
                background-color: #f39c12;
                color: white;
                font-size: 12px;
                padding: 8px 15px;
            }
            
            QPushButton[text="📁 Parcourir..."]:hover {
                background-color: #e67e22;
            }
            
            QPushButton[text="📁 Parcourir..."]:disabled {
                background-color: #ecf0f1;
                color: #95a5a6;
            }
        """)

    def _on_recovery_option_changed(self, checked: bool):
        """Gère le changement de l'option génération de clé."""
        if checked:
            self.checkbox_import_recovery.setChecked(False)

    def _on_import_option_changed(self, checked: bool):
        """Gère le changement de l'option import de clé."""
        self.btn_browse_recovery.setEnabled(checked)
        if checked:
            self.checkbox_recovery.setChecked(False)
        else:
            self.recovery_file_path = None
            self.label_recovery_file.setText("")

    def _browse_recovery_key(self):
        """Ouvre un dialogue pour sélectionner un fichier de clé de récupération."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une clé de récupération",
            "",
            "Fichiers Kripta (*.kripta);;Tous les fichiers (*.*)"
        )
        if file_path:
            self.recovery_file_path = Path(file_path)
            self.label_recovery_file.setText(f"✓ Fichier sélectionné: {self.recovery_file_path.name}")

    def _validate_and_accept(self):
        """Valide les entrées avant d'accepter."""
        password = self.edit_password.text()
        password_confirm = self.edit_password_confirm.text()

        if not password:
            self.label_error.setText("⚠ Veuillez saisir un mot de passe.")
            return

        if password != password_confirm:
            self.label_error.setText("⚠ Les mots de passe ne correspondent pas.")
            return

        if len(password) < 8:
            self.label_error.setText("⚠ Le mot de passe doit contenir au moins 8 caractères.")
            return

        if self.checkbox_import_recovery.isChecked() and not self.recovery_file_path:
            self.label_error.setText("⚠ Veuillez sélectionner un fichier de clé de récupération.")
            return

        self.accept()

    def get_values(self):
        """Retourne les valeurs saisies dans le dialogue."""
        return {
            "password": self.edit_password.text(),
            "password_confirm": self.edit_password_confirm.text(),
            "generate_recovery_key": self.checkbox_recovery.isChecked(),
            "import_recovery_key": self.checkbox_import_recovery.isChecked(),
            "recovery_key_file": self.recovery_file_path,
        }
