"""
File system scanner for disk analysis.
"""

import os
import time
from pathlib import Path
from typing import List, Set, Callable, Optional
from .models import Node, NodeType
import string


class DiskScanner:
    """Scanner de système de fichiers avec mise à jour incrémentale."""
    
    def __init__(self, progress_callback: Optional[Callable[[int, int], None]] = None):
        self.progress_callback = progress_callback
        self.scanned_count = 0
        self.total_estimate = 0
    
    @staticmethod
    def get_available_disks() -> List[str]:
        """Récupère la liste des disques disponibles (Cross-platform)."""
        drives = []
        
        if os.name == 'nt':  # Windows
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:  # Linux / Unix
            try:
                with open("/proc/mounts", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            device, mountpoint = parts[0], parts[1]
                            # Filtrer les montages système virtuels et temporaires
                            if device.startswith("/dev/") and not mountpoint.startswith(("/boot", "/snap")):
                                drives.append(mountpoint)
            except Exception:
                # Fallback simple
                if os.path.exists("/"):
                    drives.append("/")
                    
        return sorted(list(set(drives)))
    
    def scan_path(self, root_path: str, parent_id: Optional[int] = None) -> List[Node]:
        """
        Scanne récursivement un chemin et retourne la liste des nœuds.
        
        Args:
            root_path: Chemin racine à scanner
            parent_id: ID du parent dans la base de données
        
        Returns:
            Liste des nœuds trouvés
        """
        nodes = []
        
        try:
            # Estimer le nombre total de fichiers (approximatif)
            if self.total_estimate == 0:
                self.total_estimate = self._estimate_file_count(root_path)
            
            for entry in os.scandir(root_path):
                try:
                    stat = entry.stat(follow_symlinks=False)
                    
                    # Créer le nœud
                    node = Node(
                        id=None,
                        parent_id=parent_id,
                        type=NodeType.DIR if entry.is_dir(follow_symlinks=False) else NodeType.FILE,
                        name=entry.name,
                        path=entry.path,
                        size=stat.st_size if entry.is_file() else 0,
                        mtime=stat.st_mtime,
                        ctime=stat.st_ctime,
                        extension=Path(entry.name).suffix.lower() if entry.is_file() else None
                    )
                    
                    nodes.append(node)
                    self.scanned_count += 1
                    
                    # Callback de progression
                    if self.progress_callback and self.scanned_count % 100 == 0:
                        self.progress_callback(self.scanned_count, self.total_estimate)
                    
                except (PermissionError, OSError) as e:
                    # Ignorer les fichiers/dossiers inaccessibles
                    print(f"Accès refusé: {entry.path}")
                    continue
        
        except (PermissionError, OSError) as e:
            print(f"Impossible de scanner {root_path}: {e}")
        
        return nodes
    
    def _estimate_file_count(self, root_path: str, max_depth: int = 3) -> int:
        """Estime le nombre de fichiers (rapide, limité en profondeur)."""
        count = 0
        try:
            for root, dirs, files in os.walk(root_path):
                count += len(files) + len(dirs)
                # Limiter la profondeur pour l'estimation
                depth = root[len(root_path):].count(os.sep)
                if depth >= max_depth:
                    break
        except:
            pass
        
        # Multiplier par un facteur pour estimer le total
        return count * (10 if max_depth < 5 else 1)
    
    def scan_disk_incremental(self, disk_path: str, existing_paths: Set[str]) -> tuple[List[Node], Set[str]]:
        """
        Scanne un disque de manière incrémentale.
        
        Args:
            disk_path: Chemin du disque à scanner
            existing_paths: Ensemble des chemins déjà en base
        
        Returns:
            (nouveaux/modifiés nœuds, chemins vus)
        """
        nodes_to_process = []
        seen_paths = set()
        
        def scan_recursive(path: str, parent_id: Optional[int] = None):
            try:
                for entry in os.scandir(path):
                    try:
                        stat = entry.stat(follow_symlinks=False)
                        entry_path = entry.path
                        seen_paths.add(entry_path)
                        
                        # Vérifier si le fichier existe déjà
                        is_new = entry_path not in existing_paths
                        
                        node = Node(
                            id=None,
                            parent_id=parent_id,
                            type=NodeType.DIR if entry.is_dir() else NodeType.FILE,
                            name=entry.name,
                            path=entry_path,
                            size=stat.st_size if entry.is_file() else 0,
                            mtime=stat.st_mtime,
                            ctime=stat.st_ctime,
                            extension=Path(entry.name).suffix.lower() if entry.is_file() else None
                        )
                        
                        if is_new:
                            nodes_to_process.append(node)
                        
                        # Scanner récursivement les dossiers
                        if entry.is_dir():
                            scan_recursive(entry_path, None)  # parent_id sera défini après insertion
                        
                        self.scanned_count += 1
                        if self.progress_callback and self.scanned_count % 100 == 0:
                            self.progress_callback(self.scanned_count, self.total_estimate)
                    
                    except (PermissionError, OSError):
                        continue
            
            except (PermissionError, OSError):
                pass
        
        scan_recursive(disk_path)
        return nodes_to_process, seen_paths
