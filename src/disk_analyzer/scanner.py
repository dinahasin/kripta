"""
File system scanner for disk analysis.
"""

import os
import time
from pathlib import Path
from typing import List, Set, Callable, Optional
from .models import Node, NodeType
import string
import fnmatch

# Liste de base des dossiers système à ignorer
IGNORED_SYSTEM_PATHS = {
    # Linux / UNIX
    '/proc', '/sys', '/dev', '/boot', '/run', '/tmp', '/var/run', '/var/lock',
    '/lib', '/lib64', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/lib',
    '/snap',
    # Windows
    'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
    'System Volume Information', '$RECYCLE.BIN'
}

IGNORED_PATTERNS = ['*.sys', '*.dll', '*.tmp', '*.log']


class DiskScanner:
    """Scanner de système de fichiers avec mise à jour incrémentale."""
    
    def __init__(self, progress_callback: Optional[Callable[[int, int, str], None]] = None):
        self.progress_callback = progress_callback
        self.scanned_count = 0
        self.total_estimate = 0
        self._stop_requested = False
        
    def stop(self):
        """Arrête le scan en cours."""
        self._stop_requested = True
    
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
            # Estimer le nombre total de fichiers (approximatif)
            if self.total_estimate == 0:
                self.total_estimate = self._estimate_file_count(root_path)
            
            for entry in os.scandir(root_path):
                if self._stop_requested:
                    break
                    
                if self._should_ignore(entry.path):
                    continue
                    
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
                        self.progress_callback(self.scanned_count, self.total_estimate, entry.path)
                    
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
                if self._stop_requested:
                    break
                    
                # Filtrer les dossiers ignorés pour ne pas descendre dedans
                dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
                
                count += len(files) + len(dirs)
                # Limiter la profondeur pour l'estimation
                depth = root[len(root_path):].count(os.sep)
                if depth >= max_depth:
                    break
        except:
            pass
        
        # Multiplier par un facteur pour estimer le total
        return count * (10 if max_depth < 5 else 1)
    
    def scan_disk_incremental(self, disk_path: str, existing_paths: Dict[str, int], node_callback=None) -> tuple[List[Node], Set[str]]:
        """
        Scanne un disque de manière incrémentale.
        Returns: (nouveaux nodes - vide car traités par callback, chemins vus)
        """
        seen_paths = set()
        
        # Le root parent_id doit être trouvé dans existing_paths ou via le callback
        root_id = existing_paths.get(disk_path)
        if root_id is None:
            # Essayer avec ou sans slash final pour être robuste (ex: "C:" vs "C:\\")
            if disk_path.endswith(os.sep):
                root_id = existing_paths.get(disk_path.rstrip(os.sep))
            else:
                root_id = existing_paths.get(disk_path + os.sep)
                
            # Essayer aussi le slash inverse si window
            if root_id is None and os.name == 'nt':
                 alt_sep = '/' if os.sep == '\\' else '\\'
                 if disk_path.endswith(alt_sep):
                     root_id = existing_paths.get(disk_path.rstrip(alt_sep))
                 else:
                     root_id = existing_paths.get(disk_path + alt_sep)

        def scan_recursive(path: str, parent_id: Optional[int]):
            if self._stop_requested:
                return

            try:
                for entry in os.scandir(path):
                    if self._stop_requested:
                        return
                    if self._should_ignore(entry.path):
                        continue
                        
                    try:
                        stat = entry.stat(follow_symlinks=False)
                        entry_path = entry.path
                        seen_paths.add(entry_path)
                        
                        # Vérifier si le fichier existe déjà
                        # existing_paths est maintenant Dict[path, id]
                        existing_id = existing_paths.get(entry_path)
                        is_new = existing_id is None
                        
                        node = Node(
                            id=existing_id, # Peut être None si nouveau
                            parent_id=parent_id,
                            type=NodeType.DIR if entry.is_dir() else NodeType.FILE,
                            name=entry.name,
                            path=entry_path,
                            size=stat.st_size if entry.is_file() else 0,
                            mtime=stat.st_mtime,
                            ctime=stat.st_ctime,
                            extension=Path(entry.name).suffix.lower() if entry.is_file() else None
                        )
                        
                        current_id = existing_id
                        
                        if is_new:
                            # Si callback fourni, on insère tout de suite pour avoir l'ID
                            if node_callback:
                                current_id = node_callback(node)
                                node.id = current_id
                                # On met à jour le dict local pour les futurs enfants
                                existing_paths[entry_path] = current_id
                        elif node_callback:
                            # Optionnel: notifier mise à jour (taille/date)
                            # Pour l'instant on suppose que update est géré ailleurs ou pas nécessaire pour l'ID
                            pass
                        
                        # Scanner récursivement les dossiers avec le bon parent_id
                        if entry.is_dir():
                            # Si on n'a pas d'ID (ex: erreur insert), on ne peut pas lier les enfants
                            if current_id is not None:
                                scan_recursive(entry_path, current_id)
                        
                        self.scanned_count += 1
                        if self.progress_callback and self.scanned_count % 100 == 0:
                            self.progress_callback(self.scanned_count, self.total_estimate, entry.path)
                    
                    except (PermissionError, OSError):
                        continue
            
            except (PermissionError, OSError):
                pass
        
        # Démarrer le scan récursif
        # Si root_id est None, les éléments à la racine auront parent_id=None (correct pour racine disque ?)
        # Non, la racine disque elle-même a déjà été insérée par scan_disk dans sync_coordinator
        # Donc tous les éléments de scandir(disk_path) doivent avoir parent_id = root_id
        scan_recursive(disk_path, root_id)
        
        return [], seen_paths
    
    def _should_ignore(self, path: str) -> bool:
        """Vérifie si un chemin doit être ignoré."""
        path_obj = Path(path)
        
        # 1. Vérifier les dossiers système exacts (ou sous-dossiers)
        for ignored in IGNORED_SYSTEM_PATHS:
            if path.startswith(ignored):
                return True
                
        # 2. Vérifier les patterns de nom
        name = path_obj.name
        if name.startswith('.'): # Fichiers cachés par défaut
            return True
        
        for pattern in IGNORED_PATTERNS:
            if fnmatch.fnmatch(name, pattern):
                return True
                
        return False
