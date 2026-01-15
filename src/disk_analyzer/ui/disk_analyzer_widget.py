"""
Disk Analyzer Widget - UI for space optimization.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QComboBox,
                               QProgressBar, QMessageBox, QSplitter, QTabWidget, QTextEdit,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QSize
from PySide6.QtGui import QFont, QMovie, QColor, QPainter, QBrush
from pathlib import Path
from typing import Optional
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
        
    def stop(self):
        self.coordinator.stop_scan()
        self.wait()
    
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
        # Connecter le changement de sélection
        self.combo_disk.currentTextChanged.connect(self.on_disk_changed)
        toolbar_layout.addWidget(self.combo_disk)
        
        self.btn_scan = QPushButton("🔍 Scanner")
        self.btn_scan.setObjectName("btnScan")
        self.btn_scan.setMinimumHeight(28)
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan)
        toolbar_layout.addWidget(self.btn_scan)
        
        toolbar_layout.addSpacing(20)
        
        # Barre de recherche
        lbl_search = QLabel("Recherche:")
        lbl_search.setStyleSheet("font-weight: bold; color: #2c3e50;")
        toolbar_layout.addWidget(lbl_search)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Rechercher un fichier ou dossier... (regex supportée: .*test.*)")
        self.txt_search.setMinimumHeight(28)
        self.txt_search.setMaximumWidth(400)  # Limite la largeur de la recherche
        self.txt_search.returnPressed.connect(self.perform_search)
        toolbar_layout.addWidget(self.txt_search)
        
        self.btn_search = QPushButton("🔎")
        self.btn_search.setObjectName("btnSearch")
        self.btn_search.setMaximumWidth(40)
        self.btn_search.setMinimumHeight(28)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.perform_search)
        toolbar_layout.addWidget(self.btn_search)
        
        # Ajouter un stretch à la fin pour pousser tout à gauche
        toolbar_layout.addStretch()
        
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
        
        # Content area - Cette section doit s'étirer
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
        self.tree_widget.setAnimated(True)
        self.tree_widget.setIndentation(20)
        # Scroll horizontal
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tree_widget.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        self.tree_widget.itemExpanded.connect(self.on_tree_item_expanded)
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
        self.txt_details.setMaximumHeight(250)  # Augmenté pour afficher plus d'informations
        # Utiliser une police monospace pour meilleure lisibilité
        details_font = QFont("Consolas", 9)
        if not details_font.exactMatch():
            details_font = QFont("Courier New", 9)  # Alternative sur certains systèmes
        self.txt_details.setFont(details_font)
        right_layout.addWidget(self.txt_details)
        
        # Custom Disk Usage Bar
        self.disk_usage_bar = QProgressBar()
        self.disk_usage_bar.setTextVisible(True)
        self.disk_usage_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disk_usage_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid lightgrey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                margin: 0.5px;
            }
        """)
        self.disk_usage_bar.setFormat("%p% Utilisé")
        right_layout.addWidget(self.disk_usage_bar)
        
        lbl_stats = QLabel("📈 Statistiques (Top Fichiers)")
        lbl_stats.setFont(tree_font)
        lbl_stats.setStyleSheet("color: #2c3e50;")
        right_layout.addWidget(lbl_stats)
        
        # Table pour les stats avec barres visuelles
        self.table_stats = QTableWidget()
        self.table_stats.setColumnCount(4)
        self.table_stats.setHorizontalHeaderLabels(["Nom", "Barre", "Taille", "%"])
        self.table_stats.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_stats.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_stats.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_stats.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_stats.verticalHeader().setVisible(False)
        self.table_stats.setShowGrid(False)
        self.table_stats.setAlternatingRowColors(True)
        right_layout.addWidget(self.table_stats)
        
        content_splitter.addWidget(right_widget)
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(content_splitter, 1)  # Stretch factor de 1 pour cette section

    def load_disks(self):
        """Charge la liste des disques disponibles."""
        self.combo_disk.blockSignals(True)  # Éviter déclenchement intempestif
        self.combo_disk.clear()
        disks = DiskScanner.get_available_disks()
        self.combo_disk.addItems(disks)
        self.combo_disk.blockSignals(False)
        
        # Initialiser avec le premier disque si disponible
        if disks:
            self.on_disk_changed(disks[0])

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

    def on_disk_changed(self, disk_path: str):
        """Appelé quand le disque sélectionné change."""
        if not disk_path:
            return
            
        self.current_disk = disk_path
        
        # Charger les données persistantes immédiatement
        self.load_tree()
        self.load_stats()
        
    def start_scan(self):
        """Démarre le scan d'un disque."""
        disk = self.combo_disk.currentText()
        if not disk:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un disque.")
            return
        
        # S'assurer que current_disk est à jour
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
        
        # Timer pour mise à jour incrémentale de l'arborescence (chaque 1s)
        self.incremental_timer = QTimer(self)
        self.incremental_timer.timeout.connect(self.update_tree_incremental)
        self.incremental_timer.start(1000)

    def update_tree_incremental(self):
        """Met à jour l'arbre de manière incrémentale (racine + nœuds étendus)."""
        try:
            # Mise à jour de la racine
            self._update_item_children(None)
            
            # Mise à jour récursive des items étendus
            self._update_expanded_items(self.tree.invisibleRootItem())
            
        except Exception as e:
            pass # Éviter de crasher le timer

    def _update_expanded_items(self, parent_item: QTreeWidgetItem):
        """Parcourt récursivement les items étendus pour mettre à jour leurs enfants."""
        count = parent_item.childCount()
        for i in range(count):
            item = parent_item.child(i)
            # Si l'item est étendu, on met à jour ses enfants
            if item.isExpanded():
                node = item.data(0, Qt.ItemDataRole.UserRole)
                if node and node.type.name == "DIR":
                    self._update_item_children(item)
                    self._update_expanded_items(item)

    def _update_item_children(self, parent_item: QTreeWidgetItem | None):
        """Synchronise les enfants d'un item avec la DB."""
        parent_id = None
        if parent_item:
            node = parent_item.data(0, Qt.ItemDataRole.UserRole)
            # Support rétrocompatibilité
            if isinstance(node, int):
                parent_id = node
            elif node and hasattr(node, 'id'):
                parent_id = node.id
            
        # Récupérer les enfants depuis la DB
        try:
            db_children = self.coordinator.get_children(parent_id)
        except:
            return

        # Map des items existants
        existing_items = {}
        if parent_item:
            count = parent_item.childCount()
            for i in range(count):
                child = parent_item.child(i)
                node_data = child.data(0, Qt.ItemDataRole.UserRole)
                if node_data:
                    existing_items[node_data.path] = child
        else:
            count = self.tree_widget.topLevelItemCount()
            for i in range(count):
                child = self.tree_widget.topLevelItem(i)
                node_data = child.data(0, Qt.ItemDataRole.UserRole)
                if node_data:
                    existing_items[node_data.path] = child
        
        # Mettre à jour ou ajouter
        for node in db_children:
            text_size = self.format_size(node.size)
            
            if node.path in existing_items:
                # Update taille seulement si changé
                item = existing_items[node.path]
                if item.text(1) != text_size:
                    item.setText(1, text_size)
            else:
                # Nouvel item
                if parent_item:
                    item = QTreeWidgetItem(parent_item)
                else:
                    item = QTreeWidgetItem(self.tree_widget)
                
                # Ajouter des icônes pour dossiers et fichiers
                if node.type.name == "DIR":
                    item.setText(0, f"📁 {node.name}")
                else:
                    icon = self.get_file_icon(node.extension)
                    item.setText(0, f"{icon} {node.name}")
                    
                item.setText(1, text_size)
                item.setText(2, node.type.name)
                item.setData(0, Qt.ItemDataRole.UserRole, node)
                
                # Ajouter dummy si dossier pour permettre l'expansion
                if node.type.name == "DIR":
                    QTreeWidgetItem(item)

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
        
        # Arrêter le GIF et le timer
        if hasattr(self, 'incremental_timer'):
            self.incremental_timer.stop()
            
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
        
        # Normaliser le chemin du disque pour être cohérent
        from ..sqlite_service import SQLiteService
        normalized_disk = SQLiteService.normalize_path(self.current_disk)
        
        # Récupérer le nœud racine
        root_node = self.coordinator.get_node_by_path(normalized_disk)
        if not root_node:
            # Si le nœud n'existe pas, essayer de le trouver avec le chemin original
            root_node = self.coordinator.get_node_by_path(self.current_disk)
            if not root_node:
                return
        
        # NOTE: La correction de hiérarchie est désactivée au chargement pour améliorer les performances
        # Elle peut être effectuée manuellement si nécessaire, ou après un scan
        # La correction automatique ralentit trop l'ouverture de l'interface
        # Si vous voulez corriger la hiérarchie, utilisez: coordinator.fix_hierarchy(disk_path)
        
        # Créer l'item racine
        root_item = QTreeWidgetItem([f"💽 {root_node.name}", self.format_size(root_node.size), "Disque"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_node)  # Stocker le Node complet, pas juste l'ID
        self.tree_widget.addTopLevelItem(root_item)
        
        # NE PAS charger tous les enfants immédiatement - lazy loading uniquement
        # Ajouter un placeholder pour indiquer qu'il y a des enfants à charger
        if root_node.id:
            # Vérifier rapidement s'il y a des enfants sans tout charger
            has_children = self._has_children(root_node.id)
            if has_children:
                placeholder = QTreeWidgetItem(["..."])
                root_item.addChild(placeholder)
        
        # Ne pas développer automatiquement la racine - laisser l'utilisateur le faire
        # root_item.setExpanded(True)  # Commenté pour éviter le chargement automatique
        

    
    def _has_children(self, parent_id: int) -> bool:
        """Vérifie rapidement si un nœud a des enfants sans tout charger."""
        try:
            # Requête optimisée: juste compter, ne pas charger tous les nœuds
            from ..sqlite_service import SQLiteService
            cursor = self.coordinator.sqlite.conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE parent_id = ? LIMIT 1",
                (parent_id,)
            )
            result = cursor.fetchone()
            return result[0] > 0 if result else False
        except Exception:
            return False
    
    def load_tree_children(self, parent_item: QTreeWidgetItem, parent_id: int, limit: Optional[int] = None):
        """
        Charge les enfants d'un nœud dans l'arbre de manière incrémentale.
        
        Args:
            parent_item: L'item parent dans l'arbre
            parent_id: L'ID du nœud parent dans la base
            limit: Nombre maximum d'enfants à charger (None = tous, pour performance)
        """
        if not parent_id:
            return
        
        try:
            # Charger les enfants avec une limite pour améliorer les performances
            # Si limit est None, charger tous les enfants (comportement par défaut)
            if limit is None:
                children = self.coordinator.get_children(parent_id)
            else:
                # Charger seulement un nombre limité d'enfants pour les grandes arborescences
                children = self.coordinator.get_children_limited(parent_id, limit)
        except Exception as e:
            print(f"Erreur lors de la récupération des enfants pour parent_id={parent_id}: {e}")
            return
        
        if not children:
            return
        
        for child in children:
            size_str = self.format_size(child.size) if child.type == NodeType.FILE else ""
            type_str = "Dossier" if child.type == NodeType.DIR else "Fichier"
            
            item = QTreeWidgetItem([child.name, size_str, type_str])
            item.setData(0, Qt.ItemDataRole.UserRole, child)  # Stocker le Node complet, pas juste l'ID
            
            # Nom en gras
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            
            # Ajouter des icônes pour dossiers et fichiers
            if child.type == NodeType.DIR:
                item.setText(0, f"📁 {child.name}")
            else:
                # Icône basée sur l'extension
                icon = self.get_file_icon(child.extension)
                item.setText(0, f"{icon} {child.name}")
            
            parent_item.addChild(item)
            
            # Ajouter un placeholder pour les dossiers (lazy loading)
            if child.type == NodeType.DIR:
                # Vérifier rapidement s'il y a des enfants
                if child.id and self._has_children(child.id):
                    placeholder = QTreeWidgetItem(["..."])
                    item.addChild(placeholder)
    
    def on_tree_item_expanded(self, item: QTreeWidgetItem):
        """Appelé quand un item est déplié - lazy loading incrémental."""
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if not node or not hasattr(node, 'id'):
            # Support rétrocompatibilité si on a stocké juste l'ID
            node_id = node if isinstance(node, int) else None
            if not node_id:
                return
        else:
            node_id = node.id
        
        # Charger les enfants si c'est la première fois (placeholder présent)
        if item.childCount() == 1 and item.child(0).text(0) == "...":
            item.removeChild(item.child(0))
            # Charger les enfants de manière incrémentale (limite initiale pour performance)
            # On charge d'abord 100 enfants, puis on peut charger plus si nécessaire
            self.load_tree_children(item, node_id, limit=100)
    
    def on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Appelé quand un item de l'arbre est cliqué."""
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if not node:
            return
        
        # Support rétrocompatibilité si on a stocké juste l'ID
        if isinstance(node, int):
            node_id = node
        elif hasattr(node, 'id'):
            node_id = node.id
        else:
            return
        
        # Afficher les détails
        self.show_node_details(node_id)
    
    def show_node_details(self, node_id: int):
        """Affiche les détails complets d'un nœud avec taille, pourcentage, etc."""
        if not node_id:
            self.txt_details.setPlainText("Aucun nœud sélectionné.")
            return
        
        # Récupérer le nœud depuis la base de données
        node = self.coordinator.get_node_by_id(node_id)
        if not node:
            self.txt_details.setPlainText(f"Nœud avec ID {node_id} introuvable.")
            return
        
        # Récupérer les informations du disque pour calculer les pourcentages
        disk_usage = self.coordinator.get_disk_usage(self.current_disk) if self.current_disk else None
        total_disk_size = disk_usage["total"] if disk_usage else 0
        used_disk_size = disk_usage["used"] if disk_usage else 0
        
        # Construire le texte des détails
        details_lines = []
        details_lines.append("=" * 50)
        details_lines.append("📊 DÉTAILS DU NŒUD")
        details_lines.append("=" * 50)
        details_lines.append("")
        
        # Informations de base
        details_lines.append(f"📁 Nom: {node.name}")
        details_lines.append(f"🏷️  Type: {'Dossier' if node.type == NodeType.DIR else 'Fichier'}")
        details_lines.append("")
        # Chemin complet - mis en évidence
        details_lines.append("=" * 50)
        details_lines.append("📍 CHEMIN COMPLET:")
        details_lines.append("=" * 50)
        details_lines.append(node.path)
        details_lines.append("")
        details_lines.append("=" * 50)
        details_lines.append("")
        
        # Taille
        if node.type == NodeType.FILE:
            # Pour un fichier, utiliser la taille directe
            file_size = node.size
            details_lines.append(f"💾 Taille: {self.format_size(file_size)}")
        else:
            # Pour un dossier, calculer la taille récursive
            folder_size = self.coordinator.get_folder_size(node.id) if node.id else 0
            details_lines.append(f"💾 Taille (récursive): {self.format_size(folder_size)}")
            file_size = folder_size
        
        # Pourcentages
        if total_disk_size > 0:
            percent_of_total = (file_size / total_disk_size) * 100
            details_lines.append(f"📊 Pourcentage du disque total: {percent_of_total:.4f}%")
        
        if used_disk_size > 0:
            percent_of_used = (file_size / used_disk_size) * 100
            details_lines.append(f"📊 Pourcentage de l'espace utilisé: {percent_of_used:.4f}%")
        
        details_lines.append("")
        
        # Informations supplémentaires pour les dossiers
        if node.type == NodeType.DIR and node.id:
            try:
                children = self.coordinator.get_children(node.id, limit=None)
                dirs_count = sum(1 for c in children if c.type == NodeType.DIR)
                files_count = sum(1 for c in children if c.type == NodeType.FILE)
                details_lines.append(f"📂 Nombre de dossiers: {dirs_count}")
                details_lines.append(f"📄 Nombre de fichiers: {files_count}")
                details_lines.append(f"📦 Total d'éléments: {len(children)}")
                details_lines.append("")
            except Exception as e:
                details_lines.append(f"⚠️  Erreur lors du comptage: {e}")
                details_lines.append("")
        
        # Informations de date
        from datetime import datetime
        try:
            mtime_str = datetime.fromtimestamp(node.mtime).strftime("%Y-%m-%d %H:%M:%S")
            details_lines.append(f"📅 Dernière modification: {mtime_str}")
        except:
            details_lines.append(f"📅 Dernière modification: {node.mtime}")
        
        try:
            ctime_str = datetime.fromtimestamp(node.ctime).strftime("%Y-%m-%d %H:%M:%S")
            details_lines.append(f"📅 Date de création: {ctime_str}")
        except:
            details_lines.append(f"📅 Date de création: {node.ctime}")
        
        details_lines.append("")
        
        # Extension pour les fichiers
        if node.type == NodeType.FILE and node.extension:
            details_lines.append(f"🔖 Extension: {node.extension}")
            details_lines.append("")
        
        # ID technique
        details_lines.append(f"🆔 ID: {node.id}")
        if node.parent_id:
            details_lines.append(f"👆 Parent ID: {node.parent_id}")
        
        # Afficher le texte formaté
        self.txt_details.setPlainText("\n".join(details_lines))
    
    def perform_search(self):
        """Effectue une recherche avec SQLite FTS5 (support regex et full-text intelligent)."""
        query = self.txt_search.text().strip()
        if not query:
            return
        
        try:
            # Détecter automatiquement si c'est une regex
            # Les regex contiennent généralement des caractères spéciaux
            regex_chars = ['.', '*', '+', '?', '^', '$', '[', ']', '{', '}', '|', '(', ')']
            is_regex = any(char in query for char in regex_chars)
            
            # Effectuer la recherche avec support regex
            results = self.coordinator.search(query, use_tantivy=True, limit=100, use_regex=is_regex)
            
            self.tree_widget.clear()
            
            if not results:
                search_type = "regex" if is_regex else "texte"
                QMessageBox.information(
                    self, 
                    "Recherche", 
                    f"Aucun résultat trouvé.\n\nType de recherche: {search_type}"
                )
                return
            
            # Afficher les résultats directement dans l'arborescence (temps réel)
            for node in results:
                size_str = self.format_size(node.size) if node.type == NodeType.FILE else ""
                type_str = "Dossier" if node.type == NodeType.DIR else "Fichier"
                
                item = QTreeWidgetItem([node.name, size_str, type_str])
                
                # Ajouter des icônes
                if node.type == NodeType.DIR:
                    item.setText(0, f"📁 {node.name}")
                else:
                    icon = self.get_file_icon(node.extension)
                    item.setText(0, f"{icon} {node.name}")
                
                # Stocker le Node complet pour pouvoir afficher les détails avec le chemin
                item.setData(0, Qt.ItemDataRole.UserRole, node)
                # Afficher le chemin complet dans le tooltip
                item.setToolTip(0, f"Chemin complet: {node.path}")
                
                self.tree_widget.addTopLevelItem(item)
            
            # Afficher automatiquement les détails du premier résultat (avec le chemin)
            if results:
                first_item = self.tree_widget.topLevelItem(0)
                if first_item:
                    first_node = first_item.data(0, Qt.ItemDataRole.UserRole)
                    if first_node and hasattr(first_node, 'id'):
                        self.show_node_details(first_node.id)
            
            # Afficher un message informatif sur le type de recherche
            search_type = "regex" if is_regex else "texte"
            self.lbl_status.setText(f"Recherche {search_type}: {len(results)} résultat(s) trouvé(s)")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de recherche:\n{e}")
    
    def load_stats(self):
        """Charge les statistiques du disque et met à jour l'UI."""
        if not self.current_disk:
            return
            
        try:
            # 1. Espace Disque
            usage = self.coordinator.get_disk_usage(self.current_disk)
            
            percent = int(usage["percent"])
            self.disk_usage_bar.setValue(percent)
            
            used_str = self.format_size(usage["used"])
            total_str = self.format_size(usage["total"])
            free_str = self.format_size(usage["free"])
            
            self.disk_usage_bar.setFormat(f"{percent}% Utilisé ({used_str} / {total_str}) - Libre: {free_str}")
            
            # Couleur dynamique selon l'usage
            if percent < 70:
                color = "#2ecc71" # Vert
            elif percent < 90:
                color = "#f1c40f" # Jaune
            else:
                color = "#e74c3c" # Rouge
                
            self.disk_usage_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid lightgrey;
                    border-radius: 5px;
                    text-align: center;
                    color: black;
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            # 2. Top Fichiers
            top_files = self.coordinator.get_top_files(20)
            
            self.table_stats.setRowCount(0)
            
            if not top_files:
                return

            # Calculer le % relatif à l'espace UTILISÉ (pas total)
            # Ou relatif au plus gros fichier de la liste pour l'échelle visuelle
            max_size = top_files[0].size if top_files else 1
            total_used_scanned = sum(node.size for node in top_files) # Somme des top fichiers pour référence ou usage total réel
            
            # Utilisons l'espace TOTAL UTILISÉ du disque pour le % réel
            disk_used = usage["used"] if usage["used"] > 0 else 1
            
            self.table_stats.setRowCount(len(top_files))
            
            for i, node in enumerate(top_files):
                # Nom + Icône
                icon = self.get_file_icon(node.extension)
                item_name = QTableWidgetItem(f"{icon} {node.name}")
                self.table_stats.setItem(i, 0, item_name)
                
                # Taille
                item_size = QTableWidgetItem(self.format_size(node.size))
                item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_stats.setItem(i, 2, item_size)
                
                # Pourcentage (relatif à l'espace utilisé du disque)
                percent_val = (node.size / disk_used) * 100
                percent_str = f"{percent_val:.4f}%" if percent_val < 1 else f"{percent_val:.1f}%"
                
                item_percent = QTableWidgetItem(percent_str)
                item_percent.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_stats.setItem(i, 3, item_percent)
                
                # Barre visuelle (Widget custom)
                # Le max de la barre est relatif au plus gros fichier pour qu'on voit bien les différences
                bar = QProgressBar()
                bar.setMaximum(100)
                # Pour la barre visuelle, on compare au plus gros fichier de la liste (100% = le plus gros)
                # Sinon toutes les barres seraient minuscules (0.01% du disque)
                visual_percent = int((node.size / max_size) * 100)
                bar.setValue(visual_percent)
                bar.setTextVisible(False)
                bar.setStyleSheet("""
                    QProgressBar {
                        border: none;
                        background: transparent;
                        height: 10px;
                    }
                    QProgressBar::chunk {
                        background-color: #9b59b6;
                        border-radius: 2px;
                    }
                """)
                self.table_stats.setCellWidget(i, 1, bar)
                
        except Exception as e:
            QMessageBox.warning(self, "Erreur Stats", f"Impossible de charger les statistiques: {e}")
    
    @staticmethod
    def get_file_icon(extension: str) -> str:
        """Retourne une icône basée sur l'extension du fichier."""
        if not extension:
            return "📄"
        
        ext = extension.lower()
        
        # Images
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico']:
            return "🖼️"
        # Vidéos
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']:
            return "🎬"
        # Audio
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            return "🎵"
        # Archives
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return "📦"
        # Code
        elif ext in ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs']:
            return "💻"
        # Documents
        elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            return "📝"
        # Tableurs
        elif ext in ['.xls', '.xlsx', '.csv']:
            return "📊"
        # Exécutables
        elif ext in ['.exe', '.msi', '.app', '.deb', '.rpm']:
            return "⚙️"
        else:
            return "📄"
    
    @staticmethod
    def format_size(size: int) -> str:
        """Formate une taille en octets en format lisible."""
        for unit in ['o', 'Ko', 'Mo', 'Go', 'To']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} Po"
    
    def closeEvent(self, event):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
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
