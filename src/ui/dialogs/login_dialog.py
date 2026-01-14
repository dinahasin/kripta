from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt
from src.security.bootstrap import verify_master_password, load_security_profile
from src.storage.database import DB_SALT_KEY, get_or_create_db_salt, derive_database_key

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion Kripta")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.derived_key = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        lbl_info = QLabel("Veuillez entrer votre mot de passe maître :")
        layout.addWidget(lbl_info)

        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_password)

        hbox_btns = QHBoxLayout()
        btn_ok = QPushButton("Déverrouiller")
        btn_ok.clicked.connect(self.check_password)
        btn_ok.setDefault(True)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)

        hbox_btns.addWidget(btn_ok)
        hbox_btns.addWidget(btn_cancel)
        layout.addLayout(hbox_btns)

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
            # Password is correct. Now derive the database key.
            # We need the DB salt, which requires opening the DB connection temporarily 
            # (or we pass the connection in, but here we can open it).
            
            # NOTE: Ideally the DB connection management should be central.
            # For this PoC, we will let the main.py handle the DB connection creation,
            # but we need the salt here.
            
            # Let's defer the actual key derivation to the caller (main.py)
            # or do it here if we have access to the DB.
            # I will return the password and let main.py do the derivation with the DB.
            
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
            self.txt_password.clear()
            self.txt_password.setFocus()

    def get_password(self):
        return self.txt_password.text()
