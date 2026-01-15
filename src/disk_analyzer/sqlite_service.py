"""
SQLite service for hierarchical storage and analytics.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Optional, Tuple
from .models import Node, NodeType, DiskStats


class SQLiteService:
    """Service de gestion SQLite pour l'arborescence des fichiers."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalise un chemin pour garantir la cohérence dans la base de données.
        - Convertit les backslashes en slashes sur Windows (ou l'inverse selon l'OS)
        - Supprime les slashes finaux sauf pour les racines de disque
        - Résout les chemins relatifs
        """
        if not path:
            return path
        
        # Utiliser Path pour normaliser
        path_obj = Path(path)
        
        # Normaliser le chemin (résout les .., ., etc.)
        try:
            normalized = path_obj.resolve()
        except (OSError, ValueError):
            # Si le chemin n'existe pas, utiliser la normalisation de string
            normalized = path_obj
        
        # Convertir en string
        normalized_str = str(normalized)
        
        # Sur Windows, normaliser les slashes
        if os.name == 'nt':
            # Garder les backslashes pour Windows (standard)
            normalized_str = normalized_str.replace('/', '\\')
            # Pour les racines de disque (C:, D:, etc.), s'assurer qu'elles ont un backslash final
            if len(normalized_str) == 2 and normalized_str[1] == ':':
                normalized_str += '\\'
        else:
            # Sur Unix/Linux, utiliser des slashes
            normalized_str = normalized_str.replace('\\', '/')
            # S'assurer que la racine a un slash final
            if normalized_str == '/':
                pass  # Déjà correct
            elif not normalized_str.endswith('/'):
                # Pour les dossiers, on pourrait vouloir garder le slash final
                # Mais pour l'instant, on le supprime pour être cohérent
                pass
        
        return normalized_str
    
    def resolve_parent_id(self, path: str) -> Optional[int]:
        """
        Résout le parent_id d'un chemin en cherchant le parent dans la base.
        Retourne None si le parent n'existe pas ou si c'est une racine.
        """
        if not path:
            return None
        
        normalized_path = self.normalize_path(path)
        path_obj = Path(normalized_path)
        
        # Si c'est une racine (disque sur Windows ou / sur Unix), pas de parent
        if os.name == 'nt':
            # Sur Windows, une racine est de la forme "C:\"
            if len(normalized_path) == 3 and normalized_path[1] == ':' and normalized_path[2] == '\\':
                return None
        else:
            # Sur Unix, la racine est "/"
            if normalized_path == '/':
                return None
        
        # Obtenir le chemin du parent
        try:
            parent_path = str(path_obj.parent)
            # Normaliser aussi le parent
            parent_path = self.normalize_path(parent_path)
            
            # Si le parent est identique au chemin actuel, c'est une racine
            if parent_path == normalized_path:
                return None
            
            # Chercher le parent dans la base
            parent_node = self.get_node_by_path(parent_path)
            if parent_node:
                return parent_node.id
            
            # Essayer des variantes du chemin parent
            # Par exemple, si le parent est "C:" on essaie "C:\"
            if os.name == 'nt':
                if not parent_path.endswith('\\'):
                    parent_variant = parent_path + '\\'
                    parent_node = self.get_node_by_path(parent_variant)
                    if parent_node:
                        return parent_node.id
                elif parent_path.endswith('\\') and len(parent_path) > 3:
                    parent_variant = parent_path.rstrip('\\')
                    parent_node = self.get_node_by_path(parent_variant)
                    if parent_node:
                        return parent_node.id
            
            return None
        except Exception:
            return None
    
    def _initialize_db(self):
        """Initialise la base de données et crée les tables."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Table principale
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                type TEXT NOT NULL CHECK(type IN ('disk', 'dir', 'file')),
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                size INTEGER NOT NULL DEFAULT 0,
                mtime REAL NOT NULL,
                ctime REAL NOT NULL,
                extension TEXT,
                FOREIGN KEY (parent_id) REFERENCES nodes(id) ON DELETE CASCADE
            )
        """)
        
        # Index
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_parent ON nodes(parent_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON nodes(name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_extension ON nodes(extension)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON nodes(mtime)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_size ON nodes(size)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON nodes(path)")
        
        # FTS5 pour recherche full-text
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                name, path,
                content='nodes',
                content_rowid='id'
            )
        """)
        
        # Triggers pour synchroniser FTS5
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
                INSERT INTO nodes_fts(rowid, name, path) VALUES (new.id, new.name, new.path);
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
                DELETE FROM nodes_fts WHERE rowid = old.id;
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
                UPDATE nodes_fts SET name = new.name, path = new.path WHERE rowid = new.id;
            END
        """)
        
        self.conn.commit()
    
    def add_node(self, node: Node) -> int:
        """
        Ajoute un nœud et retourne son ID.
        Normalise le chemin et résout automatiquement le parent_id si nécessaire.
        Vérifie aussi que le parent_id fourni est correct.
        """
        # Normaliser le chemin
        normalized_path = self.normalize_path(node.path)
        
        # Résoudre le parent_id correct depuis le chemin
        correct_parent_id = self.resolve_parent_id(normalized_path)
        
        # Utiliser le parent_id fourni s'il existe, sinon utiliser celui résolu
        parent_id = node.parent_id
        if parent_id is None:
            parent_id = correct_parent_id
        else:
            # Vérifier que le parent_id fourni est correct
            # Si le parent_id résolu est différent, utiliser celui résolu (plus fiable)
            if correct_parent_id is not None and parent_id != correct_parent_id:
                # Vérifier que le parent_id fourni existe vraiment
                cursor_check = self.conn.execute("SELECT id FROM nodes WHERE id = ?", (parent_id,))
                if not cursor_check.fetchone():
                    # Le parent_id fourni n'existe pas, utiliser celui résolu
                    parent_id = correct_parent_id
                # Sinon, on garde le parent_id fourni (peut être valide si la hiérarchie est correcte)
        
        cursor = self.conn.execute("""
            INSERT INTO nodes (parent_id, type, name, path, size, mtime, ctime, extension)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (parent_id, node.type.value, node.name, normalized_path, 
              node.size, node.mtime, node.ctime, node.extension))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_node(self, node: Node) -> bool:
        """
        Met à jour un nœud existant.
        Met également à jour le parent_id si nécessaire (si le chemin a changé ou si parent_id est incorrect).
        """
        # Normaliser le chemin
        normalized_path = self.normalize_path(node.path)
        
        # Résoudre le parent_id correct
        correct_parent_id = self.resolve_parent_id(normalized_path)
        
        # Si le parent_id fourni est différent du parent_id résolu, utiliser le résolu
        parent_id_to_use = node.parent_id
        if correct_parent_id is not None:
            parent_id_to_use = correct_parent_id
        
        cursor = self.conn.execute("""
            UPDATE nodes SET parent_id = ?, size = ?, mtime = ?, ctime = ?
            WHERE path = ?
        """, (parent_id_to_use, node.size, node.mtime, node.ctime, normalized_path))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_node_by_path(self, path: str) -> Optional[Node]:
        """
        Récupère un nœud par son chemin.
        Essaie plusieurs variantes du chemin pour être robuste.
        """
        # Normaliser le chemin
        normalized_path = self.normalize_path(path)
        
        # Essayer d'abord avec le chemin normalisé
        cursor = self.conn.execute("""
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE path = ?
        """, (normalized_path,))
        row = cursor.fetchone()
        if row:
            return Node.from_db_row(row)
        
        # Si pas trouvé, essayer des variantes
        variations = [path]  # Le chemin original
        
        if os.name == 'nt':
            # Sur Windows, essayer avec/sans backslash final
            if normalized_path.endswith('\\') and len(normalized_path) > 3:
                variations.append(normalized_path.rstrip('\\'))
            elif not normalized_path.endswith('\\'):
                variations.append(normalized_path + '\\')
            # Essayer aussi avec des slashes normaux
            alt_path = normalized_path.replace('\\', '/')
            variations.append(alt_path)
            if alt_path.endswith('/'):
                variations.append(alt_path.rstrip('/'))
            else:
                variations.append(alt_path + '/')
        else:
            # Sur Unix, essayer avec/sans slash final
            if normalized_path.endswith('/') and normalized_path != '/':
                variations.append(normalized_path.rstrip('/'))
            elif not normalized_path.endswith('/'):
                variations.append(normalized_path + '/')
        
        # Essayer toutes les variantes
        for variant in variations:
            if variant == normalized_path:
                continue  # Déjà essayé
            cursor = self.conn.execute("""
                SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
                FROM nodes WHERE path = ?
            """, (variant,))
            row = cursor.fetchone()
            if row:
                return Node.from_db_row(row)
        
        return None
    
    def get_children(self, parent_id: int, limit: Optional[int] = None) -> List[Node]:
        """
        Récupère les enfants d'un nœud.
        
        Args:
            parent_id: ID du nœud parent
            limit: Nombre maximum d'enfants à retourner (None = tous)
        
        Returns:
            Liste des nœuds enfants
        """
        query = """
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE parent_id = ?
            ORDER BY type, name
        """
        if limit is not None:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query, (parent_id,))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def delete_node(self, path: str) -> bool:
        """Supprime un nœud et ses enfants."""
        cursor = self.conn.execute("DELETE FROM nodes WHERE path = ?", (path,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def search_fts(self, query: str, limit: int = 100) -> List[Node]:
        """Recherche full-text sur nom et chemin."""
        cursor = self.conn.execute("""
            SELECT n.id, n.parent_id, n.type, n.name, n.path, n.size, n.mtime, n.ctime, n.extension
            FROM nodes n
            JOIN nodes_fts fts ON n.id = fts.rowid
            WHERE nodes_fts MATCH ?
            LIMIT ?
        """, (query, limit))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def get_top_files(self, limit: int = 100) -> List[Node]:
        """Récupère les plus gros fichiers."""
        cursor = self.conn.execute("""
            SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
            FROM nodes WHERE type = 'file'
            ORDER BY size DESC LIMIT ?
        """, (limit,))
        return [Node.from_db_row(row) for row in cursor.fetchall()]
    
    def get_extension_stats(self) -> List[Tuple[str, int, int]]:
        """Statistiques par extension (extension, count, total_size)."""
        cursor = self.conn.execute("""
            SELECT extension, COUNT(*), SUM(size)
            FROM nodes WHERE type = 'file' AND extension IS NOT NULL
            GROUP BY extension
            ORDER BY SUM(size) DESC
        """)
        return cursor.fetchall()
    
    def get_folder_size(self, node_id: int) -> int:
        """Calcule la taille totale d'un dossier (récursif)."""
        cursor = self.conn.execute("""
            WITH RECURSIVE folder_tree AS (
                SELECT id, size FROM nodes WHERE id = ?
                UNION ALL
                SELECT n.id, n.size FROM nodes n
                JOIN folder_tree ft ON n.parent_id = ft.id
            )
            SELECT SUM(size) FROM folder_tree
        """, (node_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    
    def get_all_paths(self, parent_path: str) -> dict:
        """Récupère tous les chemins sous un parent avec leur ID."""
        normalized_parent = self.normalize_path(parent_path)
        # Utiliser LIKE avec escape pour éviter les problèmes avec les caractères spéciaux
        # Sur Windows, échapper le backslash
        if os.name == 'nt':
            # Échapper les backslashes pour LIKE
            escaped_parent = normalized_parent.replace('\\', '\\\\')
            escaped_original = parent_path.replace('\\', '\\\\')
        else:
            escaped_parent = normalized_parent.replace('/', '//')
            escaped_original = parent_path.replace('/', '//')
        
        cursor = self.conn.execute("""
            SELECT path, id FROM nodes WHERE path LIKE ? ESCAPE ? OR path LIKE ? ESCAPE ?
        """, (f"{escaped_parent}%", '\\', f"{escaped_original}%", '\\'))
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def fix_hierarchy(self, root_path: Optional[str] = None) -> int:
        """
        Corrige les parent_id incorrects dans la base de données.
        Parcourt tous les nœuds et met à jour leur parent_id en fonction de leur chemin.
        
        Args:
            root_path: Chemin racine à partir duquel corriger (None = tout corriger)
        
        Returns:
            Nombre de nœuds corrigés
        """
        fixed_count = 0
        
        # Récupérer tous les nœuds
        if root_path:
            normalized_root = self.normalize_path(root_path)
            cursor = self.conn.execute("""
                SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
                FROM nodes WHERE path LIKE ?
            """, (f"{normalized_root}%",))
        else:
            cursor = self.conn.execute("""
                SELECT id, parent_id, type, name, path, size, mtime, ctime, extension
                FROM nodes
            """)
        
        nodes = [Node.from_db_row(row) for row in cursor.fetchall()]
        
        for node in nodes:
            # Résoudre le parent_id correct
            correct_parent_id = self.resolve_parent_id(node.path)
            
            # Si le parent_id actuel est incorrect, le corriger
            if node.parent_id != correct_parent_id:
                cursor = self.conn.execute("""
                    UPDATE nodes SET parent_id = ? WHERE id = ?
                """, (correct_parent_id, node.id))
                fixed_count += 1
        
        self.conn.commit()
        return fixed_count
    
    def close(self):
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()
