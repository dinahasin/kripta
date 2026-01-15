"""
Sync coordinator for dual-data architecture (SQLite + Tantivy).
"""

from pathlib import Path
from typing import List, Optional
from .models import Node, NodeType, DiskStats
from .sqlite_service import SQLiteService
from .tantivy_service import TantivyService
from .scanner import DiskScanner
from threading import Thread, Lock


class SyncCoordinator:
    """Coordonne les opérations entre SQLite et Tantivy."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.sqlite = SQLiteService(data_dir / "disk_analyzer.db")
        self.tantivy = TantivyService(data_dir / "tantivy_index")
        self.scanner = DiskScanner()
        self.lock = Lock()
    
    def add_node(self, node: Node) -> int:
        """Ajoute un nœud dans les deux bases."""
        with self.lock:
            # Ajouter dans SQLite
            node_id = self.sqlite.add_node(node)
            node.id = node_id
            
            # Ajouter dans Tantivy (commit sera fait par batch)
            self.tantivy.add_document(node)
            
            return node_id
    
    def update_node(self, node: Node) -> bool:
        """Met à jour un nœud dans les deux bases."""
        with self.lock:
            # Mettre à jour SQLite
            success = self.sqlite.update_node(node)
            
            if success:
                # Mettre à jour Tantivy (commit sera fait par batch)
                self.tantivy.update_document(node)
            
            return success
    
    def delete_node(self, path: str) -> bool:
        """Supprime un nœud des deux bases."""
        with self.lock:
            # Supprimer de SQLite
            success = self.sqlite.delete_node(path)
            
            if success:
                # Supprimer de Tantivy (commit sera fait par batch)
                self.tantivy.delete_document(path)
            
            return success
    
    def search(self, query: str, use_tantivy: bool = True, limit: int = 100) -> List[Node]:
        """
        Recherche dans les bases.
        
        Args:
            query: Requête de recherche
            use_tantivy: Utiliser Tantivy (rapide) ou SQLite FTS5
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des nœuds trouvés
        """
        if use_tantivy:
            # Recherche Tantivy (plus rapide)
            results = self.tantivy.search(query, limit)
            # Récupérer les nœuds complets depuis SQLite
            nodes = []
            for result in results:
                node = self.sqlite.get_node_by_path(result['path'])
                if node:
                    nodes.append(node)
            return nodes
        else:
            # Recherche SQLite FTS5
            return self.sqlite.search_fts(query, limit)
    
    def get_children(self, parent_id: int) -> List[Node]:
        """Récupère les enfants d'un nœud."""
        return self.sqlite.get_children(parent_id)
    
    def get_node_by_path(self, path: str) -> Optional[Node]:
        """Récupère un nœud par son chemin."""
        return self.sqlite.get_node_by_path(path)
    
    def scan_disk(self, disk_path: str, progress_callback=None) -> None:
        """
        Scanne un disque et met à jour les bases.
        
        Args:
            disk_path: Chemin du disque à scanner
            progress_callback: Fonction de callback pour la progression
        """

        self.scanner.progress_callback = progress_callback
        self.scanner.scanned_count = 0
        
        # S'assurer que la racine existe dans la DB
        with self.lock:
            root_node = self.sqlite.get_node_by_path(disk_path)
            if not root_node:
                # Créer le nœud racine s'il n'existe pas
                try:
                    stat = Path(disk_path).stat() if Path(disk_path).exists() else None
                    root_node = Node(
                        id=None,
                        parent_id=None,
                        type=NodeType.DIR,
                        name=disk_path,
                        path=disk_path,
                        size=0,
                        mtime=stat.st_mtime if stat else 0,
                        ctime=stat.st_ctime if stat else 0,
                        extension=None
                    )
                    node_id = self.sqlite.add_node(root_node)
                    root_node.id = node_id
                    self.tantivy.add_document(root_node)
                    self.tantivy.commit()
                except Exception as e:
                    print(f"Erreur création racine {disk_path}: {e}")
        
        # Récupérer les chemins existants (avec IDs pour le liage parent-enfant)
        existing_paths = self.sqlite.get_all_paths(disk_path)
        
        # Callback d'insertion pour le scanner
        # Permet de récupérer l'ID immédiatement pour le passer aux enfants
        documents_buffer = []
        BATCH_SIZE = 1000
        
        def insert_node(node: Node) -> int:
            with self.lock:
                # SQLite (Insertion immédiate pour l'ID)
                node_id = self.sqlite.add_node(node)
                node.id = node_id
                
                # Tantivy (Batch)
                documents_buffer.append(node)
                if len(documents_buffer) >= BATCH_SIZE:
                    for doc in documents_buffer:
                        self.tantivy.add_document(doc)
                    documents_buffer.clear()
                    self.tantivy.commit()
                
                return node_id
        
        # Scanner le disque
        # new_nodes est maintenant vide car traités par le callback
        _, seen_paths = self.scanner.scan_disk_incremental(disk_path, existing_paths, node_callback=insert_node)
        
        # Flusher le reste du buffer Tantivy
        with self.lock:
            if documents_buffer:
                for doc in documents_buffer:
                    self.tantivy.add_document(doc)
                self.tantivy.commit()
                
        if self.scanner._stop_requested:
            return
        
        # Supprimer les nœuds qui n'existent plus
        deleted_paths = set(existing_paths.keys()) - seen_paths
        # Ne pas supprimer la racine
        if disk_path in deleted_paths:
            deleted_paths.remove(disk_path)
            
        if deleted_paths:
            with self.lock:
                for path in deleted_paths:
                    self.sqlite.delete_node(path)
                    self.tantivy.delete_document(path)
                
                self.tantivy.commit()
        
        # Supprimer les nœuds qui n'existent plus
        deleted_paths = existing_paths - seen_paths
        # Ne pas supprimer la racine si elle n'a pas été vue (cas du scanner qui liste les enfants)
        if disk_path in deleted_paths:
            deleted_paths.remove(disk_path)
            
        if deleted_paths:
            with self.lock:
                for path in deleted_paths:
                    self.sqlite.delete_node(path)
                    self.tantivy.delete_document(path)
                
                self.tantivy.commit()
    
    def stop_scan(self):
        """Arrête le scan en cours."""
        self.scanner.stop()

    def scan_disk_async(self, disk_path: str, progress_callback=None, completion_callback=None):
        """Scanne un disque de manière asynchrone."""
        def scan_thread():
            try:
                self.scan_disk(disk_path, progress_callback)
                if completion_callback:
                    completion_callback(True, None)
            except Exception as e:
                if completion_callback:
                    completion_callback(False, str(e))
        
        thread = Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def get_top_files(self, limit: int = 100) -> List[Node]:
        """Récupère les plus gros fichiers."""
        return self.sqlite.get_top_files(limit)
    
    def get_extension_stats(self):
        """Statistiques par extension."""
        return self.sqlite.get_extension_stats()
    
    def get_folder_size(self, node_id: int) -> int:
        """Calcule la taille d'un dossier."""
        return self.sqlite.get_folder_size(node_id)
    
    def get_disk_usage(self, path: str) -> dict:
        """Récupère l'utilisation du disque (total, used, free)."""
        import shutil
        try:
            # Sur Windows, s'assurer que le chemin est une racine de disque valide (ex: "C:\\")
            if ":" in path and len(path) <= 3:
                if not path.endswith("\\"):
                    path += "\\"
                    
            usage = shutil.disk_usage(path)
            total = usage.total
            used = usage.used
            free = usage.free
            percent = (used / total) * 100 if total > 0 else 0
            
            return {
                "total": total,
                "used": used,
                "free": free,
                "percent": percent
            }
        except Exception:
            return {"total": 0, "used": 0, "free": 0, "percent": 0}

    def close(self):
        """Ferme les connexions."""
        self.sqlite.close()
        self.tantivy.close()
