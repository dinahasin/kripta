"""
Service d'exécution en arrière-plan pour Kripta.
Gère l'exécution de l'application en arrière-plan avec support du systray.
"""

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication
from .tray_manager import TrayManager


class BackgroundService(QObject):
    """Service principal pour la gestion de l'exécution en arrière-plan."""
    
    # Signaux
    service_started = Signal()
    service_stopped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_manager = None
        self.is_running = False
        
    def initialize(self, icon=None):
        """Initialise le service en arrière-plan."""
        self.tray_manager = TrayManager(self)
        
        if self.tray_manager.setup(icon):
            self.tray_manager.show_window_requested.connect(self._on_show_window)
            self.tray_manager.quit_requested.connect(self._on_quit)
            self.tray_manager.show()
            self.is_running = True
            self.service_started.emit()
            return True
        return False
    
    def stop(self):
        """Arrête le service en arrière-plan."""
        if self.tray_manager:
            self.tray_manager.hide()
        self.is_running = False
        self.service_stopped.emit()
    
    def show_notification(self, title: str, message: str):
        """Affiche une notification système."""
        if self.tray_manager:
            self.tray_manager.show_message(title, message)
    
    def _on_show_window(self):
        """Gère la demande d'affichage de la fenêtre."""
        # Cette méthode sera connectée à la fenêtre principale
        pass
    
    def _on_quit(self):
        """Gère la demande de quitter l'application."""
        QApplication.quit()
