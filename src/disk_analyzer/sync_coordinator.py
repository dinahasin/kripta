"""
Sync coordinator for SQLite-based storage and search.
Utilise SQLite avec FTS5 pour la recherche full-text (plus simple et fiable).
"""

from pathlib import Path
from typing import List, Optional
import logging
from .models import Node, NodeType, DiskStats
from .sqlite_service import SQLiteService
from .scanner import DiskScanner
from threading import Thread, Lock


class SyncCoordinator:
    """Coordonne les opérations de stockage et recherche avec SQLite."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.sqlite = SQLiteService(data_dir / "disk_analyzer.db")
        self.scanner = DiskScanner()
        self.lock = Lock()
    
    def add_node(self, node: Node) -> int:
        """Ajoute un nœud dans SQLite."""
        with self.lock:
            node_id = self.sqlite.add_node(node)
            node.id = node_id
            return node_id
    
    def update_node(self, node: Node) -> bool:
        """Met à jour un nœud dans SQLite."""
        with self.lock:
            return self.sqlite.update_node(node)
    
    def delete_node(self, path: str) -> bool:
        """Supprime un nœud de SQLite."""
        with self.lock:
            return self.sqlite.delete_node(path)
    
    def search(self, query: str, use_tantivy: bool = True, limit: int = 100, use_regex: bool = False) -> List[Node]:
        """
        Recherche dans SQLite avec FTS5 (recherche full-text intelligente).
        
        Args:
            query: Requête de recherche (peut être une regex ou pattern glob)
            use_tantivy: Paramètre ignoré (conservé pour compatibilité)
            limit: Nombre maximum de résultats
            use_regex: Force l'utilisation de regex (détection automatique si False)
        
        Returns:
            Liste des nœuds trouvés
        """
        # Détecter si c'est une vraie regex complexe ou un pattern glob
        regex_chars = ['^', '$', '[', ']', '{', '}', '|', '(', ')', '+']
        is_complex_regex = use_regex or any(char in query for char in regex_chars)
        is_simple_glob = ('*' in query or '?' in query) and not is_complex_regex
        
        # Pour les regex complexes ou patterns glob, utiliser search_with_regex
        # Pour les recherches texte simples, utiliser FTS5 (très intelligent pour correspondances partielles)
        if is_complex_regex or is_simple_glob:
            # Recherche regex/glob avec SQLite
            return self.sqlite.search_with_regex(query, limit)
        else:
            # Recherche texte simple avec SQLite FTS5
            # FTS5 tokenise intelligemment et trouve "autodeks" dans "autodesk.iso"
            return self.sqlite.search_fts(query, limit)
    
    def get_children(self, parent_id: int, limit: Optional[int] = None) -> List[Node]:
        """
        Récupère les enfants d'un nœud.
        
        Args:
            parent_id: ID du nœud parent
            limit: Nombre maximum d'enfants à retourner (None = tous)
        
        Returns:
            Liste des nœuds enfants
        """
        return self.sqlite.get_children(parent_id, limit)
    
    def get_children_limited(self, parent_id: int, limit: int) -> List[Node]:
        """Récupère un nombre limité d'enfants d'un nœud (alias pour compatibilité)."""
        return self.sqlite.get_children(parent_id, limit)
    
    def get_node_by_id(self, node_id: int) -> Optional[Node]:
        """Récupère un nœud par son ID."""
        return self.sqlite.get_node_by_id(node_id)
    
    def get_node_by_path(self, path: str) -> Optional[Node]:
        """Récupère un nœud par son chemin (Robuste)."""
        node = self.sqlite.get_node_by_path(path)
        if node:
            return node
            
        # Essayer des variantes (C: vs C:\) pour trouver la racine
        import os
        variations = []
        if path.endswith(os.sep):
            variations.append(path.rstrip(os.sep))
        else:
            variations.append(path + os.sep)
            
        if os.name == 'nt':
            alt_sep = '/' if os.sep == '\\' else '\\'
            path_alt = path.replace(os.sep, alt_sep)
            variations.append(path_alt)
            if path_alt.endswith(alt_sep):
                 variations.append(path_alt.rstrip(alt_sep))
            else:
                 variations.append(path_alt + alt_sep)
        
        for v in variations:
            node = self.sqlite.get_node_by_path(v)
            if node:
                return node
                
        return None
    
    def scan_disk(self, disk_path: str, progress_callback=None) -> None:
        """
        Scanne un disque et met à jour les bases.
        
        Args:
            disk_path: Chemin du disque à scanner
            progress_callback: Fonction de callback pour la progression
        """

        self.scanner.progress_callback = progress_callback
        self.scanner.scanned_count = 0
        
        # Normaliser le chemin du disque
        normalized_disk_path = SQLiteService.normalize_path(disk_path)
        
        # S'assurer que la racine existe dans la DB
        with self.lock:
            root_node = self.sqlite.get_node_by_path(normalized_disk_path)
            if not root_node:
                # Créer le nœud racine s'il n'existe pas
                try:
                    stat = Path(normalized_disk_path).stat() if Path(normalized_disk_path).exists() else None
                    root_node = Node(
                        id=None,
                        parent_id=None,
                        type=NodeType.DIR,
                        name=Path(normalized_disk_path).name or normalized_disk_path,
                        path=normalized_disk_path,  # Utiliser le chemin normalisé
                        size=0,
                        mtime=stat.st_mtime if stat else 0,
                        ctime=stat.st_ctime if stat else 0,
                        extension=None
                    )
                    node_id = self.sqlite.add_node(root_node)
                    root_node.id = node_id
                except Exception as e:
                    print(f"Erreur création racine {normalized_disk_path}: {e}")
        
        # Récupérer les chemins existants (avec IDs pour le liage parent-enfant)
        # Utiliser le chemin normalisé
        existing_paths = self.sqlite.get_all_paths(normalized_disk_path)
        
        # Callback d'insertion pour le scanner
        # Permet de récupérer l'ID immédiatement pour le passer aux enfants
        def insert_node(node: Node) -> int:
            with self.lock:
                # SQLite (Insertion immédiate pour l'ID)
                node_id = self.sqlite.add_node(node)
                node.id = node_id
                return node_id
        
        # Scanner le disque (utiliser le chemin normalisé)
        _, seen_paths = self.scanner.scan_disk_incremental(normalized_disk_path, existing_paths, node_callback=insert_node)
                
        if self.scanner._stop_requested:
            return
        
        # Supprimer les nœuds qui n'existent plus
        deleted_paths = set(existing_paths.keys()) - seen_paths
        # Ne pas supprimer la racine (utiliser le chemin normalisé)
        if normalized_disk_path in deleted_paths:
            deleted_paths.remove(normalized_disk_path)
            
        if deleted_paths:
            with self.lock:
                for path in deleted_paths:
                    self.sqlite.delete_node(path)
        
        # Mettre à jour la taille du dossier racine (utiliser le chemin normalisé)
        with self.lock:
            try:
                # Rafraîchir le nœud racine
                root_node = self.sqlite.get_node_by_path(normalized_disk_path)
                if root_node and root_node.id:
                    total_size = self.sqlite.get_folder_size(root_node.id)
                    if total_size > 0:
                        root_node.size = total_size
                        self.sqlite.update_node(root_node)
            except Exception as e:
                print(f"Erreur update taille racine: {e}")

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
    
    def fix_hierarchy(self, root_path: Optional[str] = None) -> int:
        """
        Corrige les parent_id incorrects dans la base de données.
        
        Args:
            root_path: Chemin racine à partir duquel corriger (None = tout corriger)
        
        Returns:
            Nombre de nœuds corrigés
        """
        with self.lock:
            return self.sqlite.fix_hierarchy(root_path)
    
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
