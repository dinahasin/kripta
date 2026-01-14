"""
Gestionnaire de l'icône système (systray) pour l'exécution en arrière-plan.
Utilise QSystemTrayIcon pour permettre à l'application de s'exécuter en arrière-plan.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal


class TrayManager(QObject):
    """Gestionnaire de l'icône système pour l'exécution en arrière-plan."""
    
    # Signaux
    show_window_requested = Signal()
    quit_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = None
        self.menu = None
        
    def setup(self, icon: QIcon = None):
        """Configure l'icône système."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False
            
        self.tray_icon = QSystemTrayIcon(self)
        
        if icon:
            self.tray_icon.setIcon(icon)
        else:
            # Icône par défaut si aucune n'est fournie
            self.tray_icon.setIcon(QApplication.style().standardIcon(
                QApplication.style().SP_ComputerIcon
            ))
        
        self._create_menu()
        self.tray_icon.setContextMenu(self.menu)
        
        # Connexion du clic sur l'icône
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        return True
    
    def show(self):
        """Affiche l'icône dans la barre système."""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide(self):
        """Cache l'icône de la barre système."""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def set_icon(self, icon: QIcon):
        """Définit l'icône à afficher."""
        if self.tray_icon:
            self.tray_icon.setIcon(icon)
    
    def set_tooltip(self, tooltip: str):
        """Définit le texte d'aide au survol."""
        if self.tray_icon:
            self.tray_icon.setToolTip(tooltip)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, duration=5000):
        """Affiche une notification."""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)
    
    def _create_menu(self):
        """Crée le menu contextuel de l'icône système."""
        self.menu = QMenu()
        
        # Action pour afficher la fenêtre
        show_action = QAction("Afficher", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        self.menu.addAction(show_action)
        
        self.menu.addSeparator()
        
        # Action pour quitter
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)
    
    def _on_tray_activated(self, reason):
        """Gère l'activation de l'icône système."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()
