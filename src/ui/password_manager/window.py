from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QListWidgetItem, QLabel, QLineEdit, 
                               QTextEdit, QPushButton, QMessageBox, QSplitter)
from PySide6.QtCore import Qt
from src.password_manager.service import PasswordManagerService
from src.password_manager.models import PasswordEntry

class PasswordManagerWindow(QMainWindow):
    def __init__(self, service: PasswordManagerService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Kripta - Gestionnaire de Mots de Passe")
        self.resize(800, 600)
        self.current_entry_id = None
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left Side: List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_list = QLabel("Mes Mots de Passe")
        left_layout.addWidget(lbl_list)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        left_layout.addWidget(self.list_widget)
        
        btn_add = QPushButton("+ Ajouter")
        btn_add.clicked.connect(self.on_add_clicked)
        left_layout.addWidget(btn_add)

        splitter.addWidget(left_widget)

        # Right Side: Details
        right_widget = QWidget()
        self.right_widget = right_widget
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 0, 0, 0)

        # Title
        right_layout.addWidget(QLabel("Titre"))
        self.txt_title = QLineEdit()
        right_layout.addWidget(self.txt_title)

        # Username
        right_layout.addWidget(QLabel("Nom d'utilisateur"))
        self.txt_username = QLineEdit()
        right_layout.addWidget(self.txt_username)

        # Password
        right_layout.addWidget(QLabel("Mot de passe"))
        hbox_pwd = QHBoxLayout()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_toggle_pwd = QPushButton("👁")
        self.btn_toggle_pwd.setCheckable(True)
        self.btn_toggle_pwd.clicked.connect(self.toggle_password_visibility)
        self.btn_toggle_pwd.setMaximumWidth(40)
        
        hbox_pwd.addWidget(self.txt_password)
        hbox_pwd.addWidget(self.btn_toggle_pwd)
        right_layout.addLayout(hbox_pwd)

        # URL
        right_layout.addWidget(QLabel("URL"))
        self.txt_url = QLineEdit()
        right_layout.addWidget(self.txt_url)

        # Notes
        right_layout.addWidget(QLabel("Notes"))
        self.txt_notes = QTextEdit()
        right_layout.addWidget(self.txt_notes)

        # Buttons
        hbox_actions = QHBoxLayout()
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white;")
        
        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_delete.setStyleSheet("background-color: #c0392b; color: white;")
        
        hbox_actions.addWidget(self.btn_save)
        hbox_actions.addWidget(self.btn_delete)
        right_layout.addLayout(hbox_actions)

        splitter.addWidget(right_widget)
        
        # Initial state
        self.clear_form()
        self.right_widget.setEnabled(False)

    def refresh_list(self):
        self.list_widget.clear()
        entries = self.service.list_entries()
        for entry in entries:
            item = QListWidgetItem(entry.title)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        entry = self.service.get_entry(entry_id)
        if entry:
            self.load_entry_to_form(entry)
            self.right_widget.setEnabled(True)

    def load_entry_to_form(self, entry: PasswordEntry):
        self.current_entry_id = entry.id
        self.txt_title.setText(entry.title)
        self.txt_username.setText(entry.username)
        self.txt_password.setText(entry.password)
        self.txt_url.setText(entry.url)
        self.txt_notes.setText(entry.notes)

    def on_add_clicked(self):
        self.clear_form()
        self.current_entry_id = None
        self.right_widget.setEnabled(True)
        self.txt_title.setFocus()

    def clear_form(self):
        self.txt_title.clear()
        self.txt_username.clear()
        self.txt_password.clear()
        self.txt_url.clear()
        self.txt_notes.clear()
        self.current_entry_id = None
        self.btn_toggle_pwd.setChecked(False)
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)

    def on_save_clicked(self):
        title = self.txt_title.text()
        if not title:
            QMessageBox.warning(self, "Erreur", "Le titre est obligatoire.")
            return

        if self.current_entry_id:
            # Update
            entry = self.service.get_entry(self.current_entry_id)
            entry.title = title
            entry.username = self.txt_username.text()
            entry.password = self.txt_password.text()
            entry.url = self.txt_url.text()
            entry.notes = self.txt_notes.toPlainText()
            self.service.update_entry(entry)
        else:
            # Create
            self.service.add_entry(
                title=title,
                username=self.txt_username.text(),
                password=self.txt_password.text(),
                url=self.txt_url.text(),
                notes=self.txt_notes.toPlainText()
            )
        
        self.refresh_list()
        self.right_widget.setEnabled(False)
        self.clear_form()
        QMessageBox.information(self, "Succès", "Mot de passe enregistré.")

    def on_delete_clicked(self):
        if not self.current_entry_id:
            return
            
        confirm = QMessageBox.question(self, "Confirmation", "Voulez-vous vraiment supprimer cette entrée ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.service.delete_entry(self.current_entry_id)
            self.refresh_list()
            self.clear_form()
            self.right_widget.setEnabled(False)

    def toggle_password_visibility(self):
        if self.btn_toggle_pwd.isChecked():
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
