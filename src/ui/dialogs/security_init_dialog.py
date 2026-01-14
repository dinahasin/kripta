"""
Dialogues d'initialisation de la sécurité (PySide6).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QCheckBox, QFileDialog, QHBoxLayout
)
from PySide6.QtCore import Qt
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
        self.setWindowTitle("Initialisation de la sécurité - Kripta")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.label_info = QLabel(
            "Configurez votre mot de passe maître et, optionnellement, une clé de récupération."
        )
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)

        # Mot de passe
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        self.edit_password.setPlaceholderText("Mot de passe maître")
        layout.addWidget(self.edit_password)

        # Confirmation mot de passe
        self.edit_password_confirm = QLineEdit()
        self.edit_password_confirm.setEchoMode(QLineEdit.Password)
        self.edit_password_confirm.setPlaceholderText("Confirmer le mot de passe")
        layout.addWidget(self.edit_password_confirm)

        # Options de clé de récupération
        self.checkbox_recovery = QCheckBox("Générer une clé de récupération (recommandé)")
        self.checkbox_recovery.setChecked(True)
        self.checkbox_recovery.toggled.connect(self._on_recovery_option_changed)
        layout.addWidget(self.checkbox_recovery)

        # Import de clé de récupération
        recovery_layout = QHBoxLayout()
        self.checkbox_import_recovery = QCheckBox("Importer une clé de récupération existante")
        self.checkbox_import_recovery.toggled.connect(self._on_import_option_changed)
        recovery_layout.addWidget(self.checkbox_import_recovery)
        
        self.btn_browse_recovery = QPushButton("Parcourir...")
        self.btn_browse_recovery.setEnabled(False)
        self.btn_browse_recovery.clicked.connect(self._browse_recovery_key)
        recovery_layout.addWidget(self.btn_browse_recovery)
        layout.addLayout(recovery_layout)

        self.label_recovery_file = QLabel("")
        self.label_recovery_file.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.label_recovery_file)

        self.recovery_file_path = None

        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: red;")
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)

        # Boutons
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Continuer")
        self.btn_cancel = QPushButton("Annuler")
        self.btn_ok.clicked.connect(self._validate_and_accept)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

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
            self.label_recovery_file.setText(f"Fichier: {self.recovery_file_path.name}")

    def _validate_and_accept(self):
        """Valide les entrées avant d'accepter."""
        password = self.edit_password.text()
        password_confirm = self.edit_password_confirm.text()

        if not password:
            self.label_error.setText("Veuillez saisir un mot de passe.")
            return

        if password != password_confirm:
            self.label_error.setText("Les mots de passe ne correspondent pas.")
            return

        if len(password) < 8:
            self.label_error.setText("Le mot de passe doit contenir au moins 8 caractères.")
            return

        if self.checkbox_import_recovery.isChecked() and not self.recovery_file_path:
            self.label_error.setText("Veuillez sélectionner un fichier de clé de récupération.")
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
