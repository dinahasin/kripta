"""
Disk Analyzer Widget - UI for space optimization.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QComboBox,
                               QProgressBar, QMessageBox, QSplitter, QTabWidget, QTextEdit)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QMovie
from pathlib import Path
from ..sync_coordinator import SyncCoordinator
from ..scanner import DiskScanner
from ..models import Node, NodeType
from src.core.config import SECURITY_DIR
from .drive_manager_widget import DriveManagerWidget


class ScanThread(QThread):
    """Thread pour scanner un disque sans bloquer l'UI."""
    progress = Signal(int, int, str)
    finished = Signal(bool, str)
    
    def __init__(self, coordinator: SyncCoordinator, disk_path: str):
        super().__init__()
        self.coordinator = coordinator
        self.disk_path = disk_path
    
    def run(self):
        try:
            def progress_callback(current, total, filename):
                self.progress.emit(current, total, filename)
            
            self.coordinator.scan_disk(self.disk_path, progress_callback)
            self.finished.emit(True, "Scan terminé avec succès")
        except Exception as e:
            self.finished.emit(False, str(e))


class DiskAnalysisPage(QWidget):
    """Page d'analyse de disque (anciennement l'unique contenu)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialiser le coordinateur
        data_dir = SECURITY_DIR / "disk_analyzer"
        self.coordinator = SyncCoordinator(data_dir)
        
        self.scan_thread = None
        self.current_disk = None
        
        self.setup_ui()
        self.load_disks()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 10)
        toolbar_layout.setSpacing(15)
        
        # Sélection de disque
        lbl_disk = QLabel("Disque:")
        lbl_disk.setStyleSheet("font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(lbl_disk)
        
        self.combo_disk = QComboBox()
        self.combo_disk.setMinimumWidth(150)
        self.combo_disk.setMinimumHeight(35)
        toolbar_layout.addWidget(self.combo_disk)
        
        self.btn_scan = QPushButton("🔍 Scanner")
        self.btn_scan.setObjectName("btnScan")
        self.btn_scan.setMinimumHeight(35)
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan)
        toolbar_layout.addWidget(self.btn_scan)
        
        toolbar_layout.addSpacing(20)
        
        # Barre de recherche
        lbl_search = QLabel("Recherche:")
        lbl_search.setStyleSheet("font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(lbl_search)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Rechercher un fichier ou dossier...")
        self.txt_search.setMinimumHeight(35)
        self.txt_search.returnPressed.connect(self.perform_search)
        toolbar_layout.addWidget(self.txt_search, 1)
        
        self.btn_search = QPushButton("🔎")
        self.btn_search.setObjectName("btnSearch")
        self.btn_search.setMaximumWidth(40)
        self.btn_search.setMinimumHeight(35)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.perform_search)
        toolbar_layout.addWidget(self.btn_search)
        
        layout.addWidget(toolbar)
        
        # Loading area
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_loading_gif = QLabel()
        self.loading_movie = QMovie("assets/loading.gif")
        self.loading_movie.setScaledSize(self.lbl_loading_gif.sizeHint())
        self.lbl_loading_gif.setMovie(self.loading_movie)
        self.lbl_loading_gif.setVisible(False)
        loading_layout.addWidget(self.lbl_loading_gif)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        loading_layout.addWidget(self.lbl_status, 1)
        
        layout.addWidget(self.loading_container)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(5)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Tree view
        left_widget = QWidget()
        left_widget.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)
        
        lbl_tree = QLabel("📁 Arborescence")
        tree_font = QFont()
        tree_font.setPointSize(12)
        tree_font.setBold(True)
        lbl_tree.setFont(tree_font)
        lbl_tree.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(lbl_tree)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Nom", "Taille", "Type"])
        self.tree_widget.setColumnWidth(0, 250)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.tree_widget)
        
        content_splitter.addWidget(left_widget)
        
        # Right: Details and stats
        right_widget = QWidget()
        right_widget.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(15)
        
        lbl_details = QLabel("📊 Détails")
        lbl_details.setFont(tree_font)
        lbl_details.setStyleSheet("color: #2c3e50;")
        right_layout.addWidget(lbl_details)
        
        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setMaximumHeight(150)
        right_layout.addWidget(self.txt_details)
        
        lbl_stats = QLabel("📈 Statistiques")
        lbl_stats.setFont(tree_font)
        lbl_stats.setStyleSheet("color: #2c3e50;")
        right_layout.addWidget(lbl_stats)
        
        self.txt_stats = QTextEdit()
        self.txt_stats.setReadOnly(True)
        right_layout.addWidget(self.txt_stats)
        
        content_splitter.addWidget(right_widget)
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(content_splitter)

    def load_disks(self):
        """Charge la liste des disques disponibles."""
        self.combo_disk.clear()
        disks = DiskScanner.get_available_disks()
        self.combo_disk.addItems(disks)

    def select_disk(self, disk_path: str):
        """Sélectionne un disque spécifique."""
        index = self.combo_disk.findText(disk_path)
        if index >= 0:
            self.combo_disk.setCurrentIndex(index)
        else:
            # Si le disque n'est pas dans la liste (ex: vient d'être monté)
            self.load_disks()
            index = self.combo_disk.findText(disk_path)
            if index >= 0:
                self.combo_disk.setCurrentIndex(index)

    def start_scan(self):
        """Démarre le scan d'un disque."""
        disk = self.combo_disk.currentText()
        if not disk:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un disque.")
            return
        
        self.current_disk = disk
        self.btn_scan.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Activer le GIF et status
        self.lbl_loading_gif.setVisible(True)
        self.loading_movie.start()
        self.lbl_status.setText("Démarrage du scan...")
        
        # Lancer le scan dans un thread
        self.scan_thread = ScanThread(self.coordinator, disk)
        self.scan_thread.progress.connect(self.on_scan_progress)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()
    
    def on_scan_progress(self, current, total, filename):
        """Met à jour la barre de progression."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        self.lbl_status.setText(f"Scan: {filename}")
    
    def on_scan_finished(self, success, message):
        """Appelé quand le scan est terminé."""
        self.btn_scan.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Arrêter le GIF
        self.loading_movie.stop()
        self.lbl_loading_gif.setVisible(False)
        self.lbl_status.setText("")
        
        if success:
            # QMessageBox.information(self, "Succès", f"✓ {message}") # Trop intrusif
            self.load_tree()
            self.load_stats()
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du scan:\n{message}")
    
    def load_tree(self):
        """Charge l'arborescence du disque scanné."""
        self.tree_widget.clear()
        
        if not self.current_disk:
            return
        
        # Récupérer le nœud racine
        root_node = self.coordinator.get_node_by_path(self.current_disk)
        if not root_node:
            return
        
        # Créer l'item racine
        root_item = QTreeWidgetItem([root_node.name, self.format_size(root_node.size), "Disque"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_node.id)
        self.tree_widget.addTopLevelItem(root_item)
        
        # Charger les enfants
        self.load_tree_children(root_item, root_node.id)
        root_item.setExpanded(True)
    
    def load_tree_children(self, parent_item: QTreeWidgetItem, parent_id: int):
        """Charge les enfants d'un nœud dans l'arbre."""
        children = self.coordinator.get_children(parent_id)
        
        for child in children:
            size_str = self.format_size(child.size) if child.type == NodeType.FILE else ""
            type_str = "Dossier" if child.type == NodeType.DIR else "Fichier"
            
            item = QTreeWidgetItem([child.name, size_str, type_str])
            item.setData(0, Qt.ItemDataRole.UserRole, child.id)
            parent_item.addChild(item)
            
            # Ajouter un placeholder pour les dossiers (lazy loading)
            if child.type == NodeType.DIR:
                placeholder = QTreeWidgetItem(["..."])
                item.addChild(placeholder)
    
    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Appelé quand un item de l'arbre est cliqué."""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_id:
            return
        
        # Charger les enfants si nécessaire (lazy loading)
        if item.childCount() == 1 and item.child(0).text(0) == "...":
            item.removeChild(item.child(0))
            self.load_tree_children(item, node_id)
        
        # Afficher les détails
        self.show_node_details(node_id)
    
    def show_node_details(self, node_id: int):
        """Affiche les détails d'un nœud."""
        # Récupérer le nœud depuis SQLite
        # Pour l'instant, affichage simple
        self.txt_details.setPlainText(f"ID: {node_id}\n\nDétails à implémenter...")
    
    def perform_search(self):
        """Effectue une recherche avec Tantivy."""
        query = self.txt_search.text().strip()
        if not query:
            return
        
        try:
            results = self.coordinator.search(query, use_tantivy=True, limit=100)
            
            self.tree_widget.clear()
            
            if not results:
                QMessageBox.information(self, "Recherche", "Aucun résultat trouvé.")
                return
            
            # Afficher les résultats
            for node in results:
                size_str = self.format_size(node.size) if node.type == NodeType.FILE else ""
                type_str = "Dossier" if node.type == NodeType.DIR else "Fichier"
                
                item = QTreeWidgetItem([node.name, size_str, type_str])
                item.setData(0, Qt.ItemDataRole.UserRole, node.id)
                item.setToolTip(0, node.path)
                self.tree_widget.addTopLevelItem(item)
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de recherche:\n{e}")
    
    def load_stats(self):
        """Charge les statistiques du disque."""
        try:
            # Top fichiers
            top_files = self.coordinator.get_top_files(10)
            
            # Stats par extension
            ext_stats = self.coordinator.get_extension_stats()
            
            stats_text = "=== Top 10 Fichiers ===\n\n"
            for i, node in enumerate(top_files, 1):
                stats_text += f"{i}. {node.name}\n   Taille: {self.format_size(node.size)}\n\n"
            
            stats_text += "\n=== Répartition par Extension ===\n\n"
            for ext, count, total_size in ext_stats[:10]:
                stats_text += f"{ext or 'Sans extension'}: {count} fichiers, {self.format_size(total_size)}\n"
            
            self.txt_stats.setPlainText(stats_text)
        
        except Exception as e:
            self.txt_stats.setPlainText(f"Erreur lors du chargement des stats:\n{e}")
    
    @staticmethod
    def format_size(size: int) -> str:
        """Formate une taille en octets en format lisible."""
        for unit in ['o', 'Ko', 'Mo', 'Go', 'To']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} Po"
    
    def closeEvent(self, event):
        self.coordinator.close()
        super().closeEvent(event)


class DiskAnalyzerWidget(QWidget):
    """Widget principal contenant les onglets."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_modern_style()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header commun
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
        
        lbl_title = QLabel("Optimisation et Gestion d'Espace")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        lbl_title.setFont(title_font)
        lbl_title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(lbl_title)
        
        header_layout.addStretch()
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        
        # Page Analyse
        self.analysis_page = DiskAnalysisPage()
        
        # Page Gestion Disques
        self.drive_manager = DriveManagerWidget()
        
        # Connexion : Demander un scan depuis le manager
        self.drive_manager.scan_requested_from_manager.connect(self.switch_to_scan)
        
        self.tabs.addTab(self.analysis_page, "📊 Analyseur d'Espace")
        self.tabs.addTab(self.drive_manager, "💾 Gestion des Disques")
        
        main_layout.addWidget(self.tabs)
        
    def switch_to_scan(self, path: str):
        """Passe à l'onglet scan et sélectionne le chemin."""
        self.tabs.setCurrentIndex(0)
        self.analysis_page.select_disk(path)
        self.analysis_page.start_scan()
        
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
            
            QTabWidget::pane {
                border: 1px solid #ecf0f1;
                background-color: white;
            }
            
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #3498db;
                color: #3498db;
            }
            
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
            
            /* Styles hérités pour les sous-composants */
            #btnScan, #btnSearch {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
             #btnScan:hover, #btnSearch:hover {
                background-color: #2980b9;
            }
            
            QLineEdit, QComboBox, QTextEdit, QTreeWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                padding: 5px;
            }
            
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
