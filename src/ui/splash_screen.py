from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QProgressBar, QApplication, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QMovie, QPixmap, QFont, QColor, QPainter, QBrush, QPen

class SplashScreen(QWidget):
    """
    Écran de démarrage affichant les fonctionnalités principales avec des GIFs.
    """
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(700, 450)
        self.center()
        
        self.setup_ui()
        
        # Simulation de chargement
        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)  # ~3 secondes total
        
    def center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def setup_ui(self):
        # Conteneur principal avec fond blanc et coins arrondis
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        
        # Titre
        lbl_title = QLabel("KRIPTA")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 32px; font-weight: bold; color: #2c3e50; letter-spacing: 2px;")
        container_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Sécurisez. Chiffrez. Optimisez.")
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 20px;")
        container_layout.addWidget(lbl_subtitle)
        
        # Fonctionnalités (GIFs)
        features_layout = QHBoxLayout()
        features_layout.setSpacing(30)
        
        self.add_feature(features_layout, "assets/password.gif", "Coffre-fort")
        self.add_feature(features_layout, "assets/lock.gif", "Chiffrement")
        self.add_feature(features_layout, "assets/optimiser.gif", "Optimisation")
        
        container_layout.addLayout(features_layout)
        container_layout.addStretch()
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                height: 6px;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        self.progress.setTextVisible(False)
        container_layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("Initialisation...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #95a5a6; font-size: 11px; margin-top: 5px;")
        container_layout.addWidget(self.lbl_status)
        
        self.main_layout.addWidget(self.container)

    def add_feature(self, layout, gif_path, title):
        widget = QWidget()
        v_layout = QVBoxLayout(widget)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # GIF Container
        lbl_gif = QLabel()
        lbl_gif.setFixedSize(120, 120)
        lbl_gif.setStyleSheet("background-color: #f8f9fa; border-radius: 60px;")
        lbl_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        try:
            movie = QMovie(gif_path)
            movie.setScaledSize(lbl_gif.size())
            lbl_gif.setMovie(movie)
            movie.start()
        except:
            lbl_gif.setText("GIF")
            
        v_layout.addWidget(lbl_gif)
        
        # Title
        lbl_text = QLabel(title)
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_text.setStyleSheet("font-weight: bold; color: #34495e; margin-top: 10px;")
        v_layout.addWidget(lbl_text)
        
        layout.addWidget(widget)

    def update_progress(self):
        self.progress_value += 1
        self.progress.setValue(self.progress_value)
        
        if self.progress_value < 30:
            self.lbl_status.setText("Chargement des modules de sécurité...")
        elif self.progress_value < 70:
            self.lbl_status.setText("Vérification de l'intégrité des données...")
        else:
            self.lbl_status.setText("Démarrage de l'interface...")
            
        if self.progress_value >= 100:
            self.timer.stop()
            self.finished.emit()
            self.close()

    def paintEvent(self, event):
        # Ombre portée
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond transparent pour le widget parent, l'ombre est dessinée ici si on le voulait
        # Mais le stylesheet sur container fait le job pour le border
