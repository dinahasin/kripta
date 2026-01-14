from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QListWidgetItem, QLabel, QLineEdit, 
                               QTextEdit, QPushButton, QMessageBox, QSplitter, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from src.password_manager.service import PasswordManagerService
from src.password_manager.models import PasswordEntry

class PasswordManagerWidget(QWidget):
    """Widget du gestionnaire de mots de passe intégré dans la fenêtre principale."""
    
    back_requested = Signal()
    
    def __init__(self, service: PasswordManagerService, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_entry_id = None
        self.setup_ui()
        self.apply_modern_style()
        self.refresh_list()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header avec bouton retour
        header = QWidget()
        header.setObjectName("header")
        header.setMinimumHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        btn_back = QPushButton("← Retour")
        btn_back.setObjectName("btnBack")
        btn_back.setMinimumHeight(40)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(btn_back)
        
        lbl_title = QLabel("Gestionnaire de Mots de Passe")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        lbl_title.setFont(title_font)
        lbl_title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        main_layout.addWidget(header)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        content_layout.addWidget(splitter)

        # Left Side: List with modern styling
        left_widget = QWidget()
        left_widget.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
        
        # Header for list
        lbl_list = QLabel("📋 Mes Mots de Passe")
        list_font = QFont()
        list_font.setPointSize(14)
        list_font.setBold(True)
        lbl_list.setFont(list_font)
        lbl_list.setStyleSheet("color: #ffffff; padding: 10px;")
        left_layout.addWidget(lbl_list)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        left_layout.addWidget(self.list_widget)
        
        btn_add = QPushButton("➕ Ajouter un mot de passe")
        btn_add.setObjectName("btnAdd")
        btn_add.setMinimumHeight(45)
        btn_add.clicked.connect(self.on_add_clicked)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(btn_add)

        splitter.addWidget(left_widget)

        # Right Side: Details with spacious form
        right_widget = QWidget()
        right_widget.setObjectName("rightPanel")
        self.right_widget = right_widget
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(40, 30, 40, 30)
        right_layout.setSpacing(20)

        # Header
        lbl_header = QLabel("Détails du mot de passe")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        lbl_header.setFont(header_font)
        lbl_header.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
        right_layout.addWidget(lbl_header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ecf0f1; max-height: 2px;")
        right_layout.addWidget(separator)
        
        right_layout.addSpacing(10)

        # Title
        lbl_title_field = QLabel("Titre")
        lbl_title_field.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        right_layout.addWidget(lbl_title_field)
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Ex: Gmail, Facebook...")
        self.txt_title.setMinimumHeight(40)
        right_layout.addWidget(self.txt_title)

        # Username
        lbl_username = QLabel("Nom d'utilisateur / Email")
        lbl_username.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        right_layout.addWidget(lbl_username)
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Ex: utilisateur@example.com")
        self.txt_username.setMinimumHeight(40)
        right_layout.addWidget(self.txt_username)

        # Password
        lbl_password = QLabel("Mot de passe")
        lbl_password.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        right_layout.addWidget(lbl_password)
        
        hbox_pwd = QHBoxLayout()
        hbox_pwd.setSpacing(10)
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Votre mot de passe sécurisé...")
        self.txt_password.setMinimumHeight(40)
        
        self.btn_toggle_pwd = QPushButton("👁")
        self.btn_toggle_pwd.setCheckable(True)
        self.btn_toggle_pwd.clicked.connect(self.toggle_password_visibility)
        self.btn_toggle_pwd.setMaximumWidth(50)
        self.btn_toggle_pwd.setMinimumHeight(40)
        self.btn_toggle_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_pwd.setToolTip("Afficher/Masquer le mot de passe")
        
        hbox_pwd.addWidget(self.txt_password)
        hbox_pwd.addWidget(self.btn_toggle_pwd)
        right_layout.addLayout(hbox_pwd)

        # URL
        lbl_url = QLabel("URL / Site web")
        lbl_url.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        right_layout.addWidget(lbl_url)
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://example.com")
        self.txt_url.setMinimumHeight(40)
        right_layout.addWidget(self.txt_url)

        # Notes
        lbl_notes = QLabel("Notes")
        lbl_notes.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        right_layout.addWidget(lbl_notes)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Informations supplémentaires...")
        self.txt_notes.setMinimumHeight(80)
        right_layout.addWidget(self.txt_notes)

        # Spacer
        right_layout.addStretch()

        # Buttons
        hbox_actions = QHBoxLayout()
        hbox_actions.setSpacing(15)
        
        self.btn_delete = QPushButton("🗑 Supprimer")
        self.btn_delete.setObjectName("btnDelete")
        self.btn_delete.setMinimumHeight(45)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_save = QPushButton("💾 Enregistrer")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setMinimumHeight(45)
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        
        hbox_actions.addWidget(self.btn_delete)
        hbox_actions.addWidget(self.btn_save)
        right_layout.addLayout(hbox_actions)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addLayout(content_layout)
        
        # Initial state
        self.clear_form()
        self.right_widget.setEnabled(False)

    def apply_modern_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
            }
            
            #header {
                background-color: #ffffff;
                border-bottom: 2px solid #ecf0f1;
            }
            
            #btnBack {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            
            #btnBack:hover {
                background-color: #d5dbdb;
            }
            
            #leftPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-right: 1px solid #dfe4ea;
            }
            
            #rightPanel {
                background-color: #ffffff;
            }
            
            QListWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 10px;
                padding: 5px;
                color: #ffffff;
                font-size: 13px;
            }
            
            QListWidget::item {
                padding: 15px;
                border-radius: 8px;
                margin: 3px 0px;
            }
            
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            
            QListWidget::item:selected {
                background-color: rgba(52, 152, 219, 0.3);
                font-weight: bold;
                border-left: 3px solid #3498db;
            }
            
            QLineEdit, QTextEdit {
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 13px;
                background-color: #f8f9fa;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3498db;
                background-color: #ffffff;
            }
            
            QTextEdit {
                padding: 10px;
            }
            
            QPushButton {
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            
            #btnAdd {
                background-color: rgba(255, 255, 255, 0.2);
                color: #ffffff;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            
            #btnAdd:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            
            #btnSave {
                background-color: #27ae60;
                color: white;
            }
            
            #btnSave:hover {
                background-color: #229954;
            }
            
            #btnSave:pressed {
                background-color: #1e8449;
            }
            
            #btnDelete {
                background-color: #e74c3c;
                color: white;
            }
            
            #btnDelete:hover {
                background-color: #c0392b;
            }
            
            #btnDelete:pressed {
                background-color: #a93226;
            }
            
            QPushButton[text="👁"] {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
            }
            
            QPushButton[text="👁"]:hover {
                background-color: #d5dbdb;
            }
            
            QPushButton[text="👁"]:checked {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
            }
        """)

    def refresh_list(self):
        self.list_widget.clear()
        entries = self.service.list_entries()
        for entry in entries:
            item = QListWidgetItem(f"🔑 {entry.title}")
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
        QMessageBox.information(self, "Succès", "✓ Mot de passe enregistré avec succès !")

    def on_delete_clicked(self):
        if not self.current_entry_id:
            return
            
        confirm = QMessageBox.question(self, "Confirmation", 
                                     "⚠ Voulez-vous vraiment supprimer cette entrée ?\n\nCette action est irréversible.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.service.delete_entry(self.current_entry_id)
            self.refresh_list()
            self.clear_form()
            self.right_widget.setEnabled(False)
            QMessageBox.information(self, "Suppression", "✓ Entrée supprimée avec succès.")

    def toggle_password_visibility(self):
        if self.btn_toggle_pwd.isChecked():
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
