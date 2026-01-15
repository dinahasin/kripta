from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QColor

from ..drive_service import DriveService, DriveInfo

class DriveWidget(QFrame):
    """Widget représentant un seul disque/partition."""
    
    scan_requested = Signal(str)  # Signal émis quand on clique sur "Scanner"
    
    def __init__(self, drive: DriveInfo, parent=None):
        super().__init__(parent)
        self.drive = drive
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            DriveWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            DriveWidget:hover {
                border: 1px solid #3498db;
                background-color: #f8fcfd;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Icone
        icon_label = QLabel()
        icon_char = "💾" if not self.drive.is_removable else "🔌"
        if self.drive.is_system:
            icon_char = "🖥️"
        
        icon_label.setText(icon_char)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        layout.addWidget(icon_label)
        
        # Infos
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(f"{self.drive.name} ({self.drive.device})")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        info_layout.addWidget(name_label)
        
        details = f"{self.drive.size} • {self.drive.type}"
        if self.drive.is_mounted:
            details += f" • {self.drive.mountpoint}"
        else:
            details += " • Non monté"
            
        details_label = QLabel(details)
        details_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout, 1) # Stretch pour pousser les boutons à droite
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        # Bouton Scan (seulement si monté)
        if self.drive.is_mounted:
            btn_scan = QPushButton("🔍 Analyser")
            btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_scan.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #bdc3c7;
                }
            """)
            btn_scan.clicked.connect(lambda: self.scan_requested.emit(self.drive.mountpoint))
            btn_layout.addWidget(btn_scan)
        
        # Bouton Mount/Unmount
        if self.drive.is_mounted:
            # Ne pas permettre de démonter le disque système
            if not self.drive.is_system:
                btn_action = QPushButton("⏏ Démonter")
                btn_action.setStyleSheet("""
                    QPushButton {
                        background-color: #fff3cd;
                        color: #856404;
                        border: 1px solid #ffeeba;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #ffeeba;
                    }
                """)
                btn_action.clicked.connect(self.unmount)
                btn_layout.addWidget(btn_action)
        else:
            btn_action = QPushButton("⚡ Monter")
            btn_action.setStyleSheet("""
                QPushButton {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #c3e6cb;
                }
            """)
            btn_action.clicked.connect(self.mount)
            btn_layout.addWidget(btn_action)
            
        # Bouton Eject pour amovibles
        if self.drive.is_removable and not self.drive.is_mounted:
            btn_eject = QPushButton("👋 Éjecter")
            btn_eject.setStyleSheet("""
                QPushButton {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #f5c6cb;
                }
            """)
            btn_eject.clicked.connect(self.power_off)
            btn_layout.addWidget(btn_eject)
            
        layout.addLayout(btn_layout)

    def mount(self):
        if DriveService.mount_drive(self.drive.device):
            self.parent().refresh_drives()  # type: ignore
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible de monter {self.drive.device}")

    def unmount(self):
        if DriveService.unmount_drive(self.drive.device):
            self.parent().refresh_drives()  # type: ignore
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible de démonter {self.drive.device}")

    def power_off(self):
        if DriveService.power_off_drive(self.drive.device):
            QMessageBox.information(self, "Succès", "Vous pouvez retirer le périphérique en toute sécurité.")
            self.parent().refresh_drives()  # type: ignore
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible d'éjecter {self.drive.device}")


class DriveManagerWidget(QWidget):
    """Widget principal de gestion des disques."""
    
    scan_requested_from_manager = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_drives()
        
        # Rafraîchissement auto
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_drives)
        self.timer.start(5000) # Toutes les 5s

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Gestion des Disques")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_drives)
        header_layout.addWidget(btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Zone de scroll pour la liste
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent;")
        
        self.scroll_content = QWidget()
        self.drives_layout = QVBoxLayout(self.scroll_content)
        self.drives_layout.setSpacing(10)
        self.drives_layout.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    def refresh_drives(self):
        """Met à jour la liste des disques."""
        drives = DriveService.get_drives()
        
        # Nettoyer l'existant
        self._clear_layout(self.drives_layout)
        
        if not drives:
            lbl_empty = QLabel("Aucun disque détecté")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: #7f8c8d; font-size: 14px; margin-top: 50px;")
            self.drives_layout.addWidget(lbl_empty)
        
        # Séparer les disques pour l'affichage (système vs amovibles/autres)
        system_drives = [d for d in drives if d.is_system]
        other_drives = [d for d in drives if not d.is_system]
        
        # Afficher les autres disques en premier (plus utile pour l'utilisateur)
        if other_drives:
            lbl_removable = QLabel("Disques Externes / Données")
            lbl_removable.setStyleSheet("font-weight: bold; color: #7f8c8d; margin-top: 10px; margin-bottom: 5px;")
            self.drives_layout.addWidget(lbl_removable)
            
            for drive in other_drives:
                widget = DriveWidget(drive, self)
                widget.scan_requested.connect(self.scan_requested_from_manager.emit)
                self.drives_layout.addWidget(widget)
                
        if system_drives:
            lbl_sys = QLabel("Disques Système")
            lbl_sys.setStyleSheet("font-weight: bold; color: #7f8c8d; margin-top: 20px; margin-bottom: 5px;")
            self.drives_layout.addWidget(lbl_sys)
            
            for drive in system_drives:
                widget = DriveWidget(drive, self)
                widget.scan_requested.connect(self.scan_requested_from_manager.emit)
                self.drives_layout.addWidget(widget)
                
        self.drives_layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
